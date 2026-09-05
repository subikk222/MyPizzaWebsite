from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import Order, OrderItem, Product, db
from auth_jwt import admin_required

admin_orders_bp = Blueprint("admin_orders", __name__)

ALLOWED_STATUSES = {"new", "preparing", "delivered", "cancelled"}


def _sync_order_items(order):
    items = OrderItem.query.filter_by(order_id=order.id).all()
    unit_price = (
        round(order.total_price / order.quantity, 2)
        if order.quantity
        else order.total_price
    )

    if len(items) == 1:
        items[0].quantity = order.quantity
        items[0].price = unit_price
        return

    if len(items) > 1:
        product_id = items[0].product_id
        for item in items:
            db.session.delete(item)
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product_id,
            quantity=order.quantity,
            price=unit_price,
        ))
        return

    pizza_name = (order.pizza or "").split(",")[0].strip()
    product = Product.query.filter_by(name=pizza_name).first()
    if product:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=order.quantity,
            price=unit_price,
        ))


@admin_orders_bp.route("/admin/orders", methods=["GET"])
@admin_required
def list_orders():
    orders = Order.query.order_by(Order.id.desc()).all()
    for order in orders:
        if order.status == "delivered":
            order.arrival_text = "Delivered"
        elif order.status == "cancelled":
            order.arrival_text = "Cancelled"
        elif order.status == "preparing":
            order.arrival_text = "Preparing"
        else:
            order.arrival_text = "New"
    return render_template("admin_orders.html", orders=orders)


@admin_orders_bp.route("/admin/orders/<int:order_id>", methods=["GET", "POST"])
@admin_required
def edit_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found", "danger")
        return redirect(url_for("admin_orders.list_orders"))

    if request.method == "POST":
        order.customer_name = (request.form.get("customer_name") or order.customer_name).strip()
        order.customer_email = (request.form.get("customer_email") or order.customer_email).strip()
        order.pizza = (request.form.get("pizza") or order.pizza).strip()

        try:
            order.quantity = int(request.form.get("quantity", order.quantity))
            order.total_price = float(request.form.get("total_price", order.total_price))
        except (TypeError, ValueError):
            flash("Quantity and Total Price must be numbers", "danger")
            return render_template("admin_order_edit.html", order=order)

        if order.quantity < 1:
            flash("Quantity less 1.", "danger")
            return render_template("admin_order_edit.html", order=order)

        new_status = request.form.get("status", order.status)
        if new_status not in ALLOWED_STATUSES:
            flash("Invalid Status.", "danger")
            return render_template("admin_order_edit.html", order=order)

        order.status = new_status
        _sync_order_items(order)
        db.session.commit()
        flash("Order updated successfully!", "success")
        return redirect(url_for("admin_orders.list_orders"))

    return render_template("admin_order_edit.html", order=order)
