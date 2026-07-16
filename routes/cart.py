from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

from models import Product, Order, User, db

import stripe

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/cart")
def cart():
    cart_items = session.get("cart", [])

    for item in cart_items:
        if "qty" not in item:
            item["qty"] = 1

    session.modified = True
    total = sum(item["price"] * item["qty"] for item in cart_items)

    return render_template("cart.html", cart=cart_items, total=total)


@cart_bp.route("/add_cart/<int:pizza_id>", methods=["POST"])
def add_cart(pizza_id):
    quantity = max(1, int(request.form.get("quantity", 1)))
    pizza = db.session.get(Product, pizza_id)

    if not pizza:
        flash("Invalid pizza id")
        return redirect(url_for("shop.index"))

    if "cart" not in session:
        session["cart"] = []

    for item in session["cart"]:
        if item["id"] == pizza_id:
            item["qty"] += quantity
            session.modified = True
            return redirect(url_for("cart.cart"))

    session["cart"].append({
        "id": pizza.id,
        "name": pizza.name,
        "price": pizza.price,
        "qty": quantity,
    })

    session.modified = True
    return redirect(url_for("shop.index"))


@cart_bp.route("/update_quantity/<int:index>/<string:action>", methods=["POST"])
def update_quantity(index, action):
    if "cart" in session and 0 <= index < len(session["cart"]):
        if action == "plus":
            session["cart"][index]["qty"] += 1
        elif action == "minus":
            session["cart"][index]["qty"] -= 1
            if session["cart"][index]["qty"] <= 0:
                session["cart"].pop(index)

        session.modified = True

    return redirect(url_for("cart.cart"))


@cart_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    cart_items = session.get("cart", [])

    if not cart_items:
        return redirect(url_for("cart.cart"))

    line_items = []
    for item in cart_items:
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {"name": item["name"]},
                "unit_amount": int(item["price"] * 100),
            },
            "quantity": item["qty"],
        })

    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=url_for("cart.success", _external=True),
        cancel_url=url_for("cart.cancel", _external=True),
    )

    return redirect(checkout_session.url)


@cart_bp.route("/success")
def success():
    cart_items = session.get("cart", [])

    if cart_items:
        total = sum(item["price"] * item["qty"] for item in cart_items)

        user = None

        if "user_id" in session:
            user = db.session.get(User, session["user_id"])

        order = Order(
            user_id=user.id if user else None,
            customer_name=user.name if user else "Guest",
            customer_email=user.email if user else "guest@example.com",
            total_price=total,
        )

        db.session.add(order)
        db.session.commit()

    session.pop("cart", None)

    return render_template("success.html")


@cart_bp.route("/cancel")
def cancel():
    return render_template("cancel.html")
