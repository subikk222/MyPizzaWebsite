from flask import Blueprint, render_template, session, redirect, url_for, flash
from models import Order, db
from datetime import datetime, timedelta

userorders_bp = Blueprint("userorders", __name__)


@userorders_bp.route("/myorders")
def my_orders():
    if "user_id" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
    now = datetime.utcnow()
    for order in orders:
        if order.status == "new":
            order.arrival_text = "Your delivery will arrive in 10 seconds"
        elif order.status == "preparing":
            order.arrival_text = "Your delivery will arrive in 5 seconds"
        elif order.status == "delivered":
            order.arrival_text = "Your delivery arrived"
        else:
            order.arrival_text = "Your delivery canceled"
    return render_template("userorders.html", orders=orders)