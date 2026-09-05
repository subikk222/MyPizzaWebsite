from datetime import datetime, timedelta

from flask import Blueprint, render_template

from models import Order, db
from auth_jwt import login_required, get_current_user

user_orders_bp = Blueprint("user_orders", __name__)

DELIVERY_AFTER = timedelta(hours=2)


def _order_created_at(order):
    created = order.created_at
    if created is None:
        return datetime.utcnow()
    if created.tzinfo is not None:
        return created.replace(tzinfo=None)
    return created


def _format_remaining(seconds_left):
    hours = seconds_left // 3600
    minutes = (seconds_left % 3600) // 60
    seconds = seconds_left % 60
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def advance_order_timer(order, now=None):
    """Якщо минуло 2+ години з created_at — статус delivered."""
    now = now or datetime.utcnow()

    if order.status == "cancelled":
        order.seconds_left = 0
        order.arrival_text = "Your delivery canceled"
        return

    if order.status == "delivered":
        order.seconds_left = 0
        order.arrival_text = "Delivered"
        return

    created = _order_created_at(order)
    arrive_time = created + DELIVERY_AFTER
    seconds_left = int((arrive_time - now).total_seconds())

    if seconds_left > 0:
        order.seconds_left = seconds_left
        order.arrival_text = f"Arrives in {_format_remaining(seconds_left)}"
    else:
        order.status = "delivered"
        order.seconds_left = 0
        order.arrival_text = "Delivered"


@user_orders_bp.route("/myorders")
@login_required
def my_orders():
    user = get_current_user()
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.id.desc()).all()
    now = datetime.utcnow()
    changed = False

    for order in orders:
        old_status = order.status
        advance_order_timer(order, now)
        if order.status != old_status:
            changed = True

    if changed:
        db.session.commit()

    return render_template("user_orders.html", orders=orders)
