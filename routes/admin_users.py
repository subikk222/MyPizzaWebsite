from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
import bcrypt

from models import User, db
from auth_jwt import admin_required, get_current_user

admin_users_bp = Blueprint("admin_users", __name__)

ALLOWED_ROLES = {"user", "admin"}


@admin_users_bp.route("/admin/users", methods=["GET"])
@admin_required
def list_users():
    users = User.query.order_by(User.id.asc()).all()
    return render_template("admin_users.html", users=users)


@admin_users_bp.route("/admin/users/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("admin_users.list_users"))

    current = get_current_user()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        role = (request.form.get("role") or user.role).strip()
        new_password = request.form.get("new_password") or ""

        if not name:
            flash("Name cannot be empty.", "danger")
            return render_template("admin_user_edit.html", user=user)

        if not email or "@" not in email:
            flash("Enter a valid email address.", "danger")
            return render_template("admin_user_edit.html", user=user)

        if role not in ALLOWED_ROLES:
            flash("Invalid role.", "danger")
            return render_template("admin_user_edit.html", user=user)

        # не можна зняти собі роль admin
        if current and current.id == user.id and role != "admin":
            flash("You cannot remove your own admin role.", "danger")
            return render_template("admin_user_edit.html", user=user)

        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            flash("This email is already in use.", "danger")
            return render_template("admin_user_edit.html", user=user)

        user.name = name
        user.phone = phone
        user.email = email
        user.role = role

        if new_password:
            if len(new_password) < 6:
                flash("Password must contain at least 6 characters.", "danger")
                return render_template("admin_user_edit.html", user=user)

            if role == "admin":
                user.password = bcrypt.hashpw(
                    new_password.encode("utf-8"),
                    bcrypt.gensalt(),
                ).decode("utf-8")
            else:
                user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("admin_users.list_users"))

    return render_template("admin_user_edit.html", user=user)
