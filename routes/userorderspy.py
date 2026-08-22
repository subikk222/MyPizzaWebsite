from datetime import datetime

from flask import Blueprint, render_template, session, redirect, url_for, flash

from models import Order, db

userorders_bp = Blueprint("userorders", __name__)

# new: 10 сек → preparing: 5 сек → delivered
NEW_SECONDS = 10
PREPARING_SECONDS = 5
TOTAL_SECONDS = NEW_SECONDS + PREPARING_SECONDS


def _order_created_at(order):
    created = order.created_at
    if created is None:
        return datetime.utcnow()
    # SQLite часто віддає naive datetime
    if created.tzinfo is not None:
        return created.replace(tzinfo=None)
    return created


def advance_order_timer(order, now=None):
    """Оновлює статус замовлення за часом і повертає секунди до наступної зміни / доставки."""
    now = now or datetime.utcnow()

    if order.status == "cancelled":
        order.seconds_left = 0
        order.arrival_text = "Your delivery canceled"
        return

    if order.status == "delivered":
        order.seconds_left = 0
        order.arrival_text = "Your delivery arrived"
        return

    created = _order_created_at(order)
    elapsed = max(0, (now - created).total_seconds())

    if elapsed < NEW_SECONDS:
        order.status = "new"
        order.seconds_left = int(NEW_SECONDS - elapsed)
        order.arrival_text = f"Your delivery will arrive in {order.seconds_left} seconds"
    elif elapsed < TOTAL_SECONDS:
        order.status = "preparing"
        order.seconds_left = int(TOTAL_SECONDS - elapsed)
        order.arrival_text = f"Your delivery will arrive in {order.seconds_left} seconds"
    else:
        order.status = "delivered"
        order.seconds_left = 0
        order.arrival_text = "Your delivery arrived"


@userorders_bp.route("/myorders")
def my_orders():
    if "user_id" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
    now = datetime.utcnow()
    changed = False

    for order in orders:
        old_status = order.status
        advance_order_timer(order, now)
        if order.status != old_status and old_status != "cancelled":
            changed = True

    if changed:
        db.session.commit()

    return render_template("userorders.html", orders=orders)
