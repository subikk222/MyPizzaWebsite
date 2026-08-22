from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import Order, db

edit_bp = Blueprint("edit", __name__)


@edit_bp.route('/editpayment', methods=['GET', 'POST'])
def edit():
    if session.get("user_role") != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("shop.index"))

    orders = Order.query.order_by(Order.id.desc()).all()

    return render_template("edit.html", orders=orders)


@edit_bp.route('/editpayment/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    if session.get("user_role") != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("shop.index"))

    order = db.session.get(Order, order_id)

    if not order:
        flash("Order not found", "danger")
        return redirect(url_for("edit.edit"))

    if request.method == "POST":
        order.customer_name = request.form.get("customer_name", order.customer_name)
        order.customer_email = request.form.get("customer_email", order.customer_email)
        order.pizza = request.form.get("pizza", order.pizza)
        order.quantity = int(request.form.get("quantity", order.quantity))
        order.total_price = float(request.form.get("total_price", order.total_price))
        order.status = request.form.get("status", order.status)

        db.session.commit()
        flash("Order updated successfully!", "success")
        return redirect(url_for("edit.edit"))

    return render_template("edit_order.html", order=order)