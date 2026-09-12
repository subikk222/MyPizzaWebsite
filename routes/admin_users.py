from flask import Blueprint, render_template, request, redirect, url_for, flash
from auth_jwt import admin_required

admin_users_bp = Blueprint("admin_users", __name__)

@admin_users_bp("/admin/edituser", methods=["GET, POST"])
@admin_required
def edit_user():
    return render_template("admin_edit_user.html")