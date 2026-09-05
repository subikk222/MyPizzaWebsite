from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    current_app,
)
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import logging

from models import User, db
from auth_jwt import (
    create_token,
    get_current_user,
    set_auth_cookie,
    clear_auth_cookie,
    login_required,
    admin_required,
    token_required,
    admin_token_required,
)

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def _verify_password(user, password):
    if user.role == "admin":
        return bcrypt.checkpw(
            password.encode("utf-8"),
            user.password.encode("utf-8"),
        )
    return check_password_hash(user.password, password)


def _login_success_response(user, *, json_mode=False):
    token = create_token(user)
    ttl = int(current_app.config.get("JWT_TTL_SECONDS", 7200))
    logger.info("[JWT] login ok: user_id=%s role=%s", user.id, user.role)

    if json_mode:
        response = make_response(
            jsonify({
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": ttl,
                "user": user.to_dict(),
            })
        )
    else:
        if user.role == "admin":
            target = url_for("auth.profile_admin")
        else:
            target = url_for("auth.profile")
        response = make_response(redirect(target))

    set_auth_cookie(response, token)
    return response


# --- Web: login, registration, profile ---


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and _verify_password(user, password):
            return _login_success_response(user, json_mode=False)

        logger.info("[JWT] login failed: %s", email or "(empty)")
        flash("Invalid email or password", "danger")

    return render_template("login.html")


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    """JSON login for Postman / API clients. Returns Bearer JWT."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not _verify_password(user, password):
        logger.info("[JWT] api login failed: %s", email or "(empty)")
        return jsonify({"error": "Invalid email or password"}), 401

    return _login_success_response(user, json_mode=True)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        password_text = request.form["password"]
        admin_code = request.form.get("admin_code")

        if admin_code == "pizza_admin":
            role = "admin"
            password = bcrypt.hashpw(
                password_text.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")
        else:
            role = "user"
            password = generate_password_hash(password_text)

        if User.query.filter_by(email=email).first():
            flash("This user already exists.", "danger")
            return render_template("register.html")

        user = User(name=name, phone=phone, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash("Thank you for registering. Please login.", "info")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/profile")
@login_required
def profile():
    user = get_current_user()
    return render_template("profile.html", user=user)


@auth_bp.route("/profileadmin")
@admin_required
def profile_admin():
    user = get_current_user()
    return render_template("profileadmin.html", name=user.name)


@auth_bp.route("/logout")
def logout():
    response = make_response(redirect(url_for("shop.index")))
    clear_auth_cookie(response)
    logger.info("[JWT] logout")
    return response


@auth_bp.route("/reset_name", methods=["POST"])
@login_required
def reset_name():
    user = get_current_user()
    new_name = (request.form.get("new_name") or "").strip()
    if not new_name:
        flash("The Name can't be empty.", "danger")
        return redirect(url_for("auth.profile"))

    user.name = new_name
    db.session.commit()
    flash("The Name is successfully updated.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/reset_number", methods=["POST"])
@login_required
def reset_number():
    user = get_current_user()
    new_number = (request.form.get("new_number") or "").strip()
    if not new_number.isdigit():
        flash("The Phone Number can't be empty.", "danger")
        return redirect(url_for("auth.profile"))

    user.phone = new_number
    db.session.commit()
    flash("The Phone Number is successfully updated.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/reset_email", methods=["POST"])
@login_required
def reset_email():
    user = get_current_user()
    new_email = (request.form.get("new_email") or "").strip().lower()
    if not new_email or "@" not in new_email:
        flash("Enter a valid email address.", "danger")
        return redirect(url_for("auth.profile"))

    existing = User.query.filter_by(email=new_email).first()
    if existing and existing.id != user.id:
        flash("This email is already in use by another account.", "danger")
        return redirect(url_for("auth.profile"))

    user.email = new_email
    db.session.commit()
    flash("Email is successfully updated.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/reset_password", methods=["POST"])
@login_required
def reset_password():
    user = get_current_user()
    new_password = request.form.get("new_password") or ""
    if len(new_password) < 6:
        flash("The password must contain at least 6 characters.", "danger")
        return redirect(url_for("auth.profile"))

    if user.role == "admin":
        user.password = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
    else:
        user.password = generate_password_hash(new_password)

    db.session.commit()
    flash("Password is successfully updated.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/api/me")
@token_required
def api_me():
    """Protected probe endpoint — like /api/protected in the JWT demo."""
    user = request.user
    payload = request.jwt_payload
    return jsonify({
        "message": f"Hello, {user.name}!",
        "user": user.to_dict(),
        "role": user.role,
        "expires_at": payload.get("exp"),
    })


# --- JSON: CRUD users (Postman) — requires JWT; mutations require admin ---


@auth_bp.route("/users", methods=["GET"])
@token_required
def get_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([user.to_dict() for user in users])


@auth_bp.route("/users", methods=["POST"])
@admin_token_required
def create_user():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    password = (data.get("password") or "").strip()

    if not name or not email:
        return jsonify({"error": "The Name and Email fields are required"}), 400

    user = User(
        name=name,
        email=email,
        phone=phone,
        password=generate_password_hash(password) if password else "",
    )
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@auth_bp.route("/users/<int:user_id>", methods=["GET"])
@token_required
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User Not Found"}), 404

    return jsonify(user.to_dict())


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_token_required
def update_user_put(user_id):
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not email:
        return jsonify({"error": "The Name and Email fields are required"}), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User Not Found"}), 404

    user.name = name
    user.email = email
    db.session.commit()

    return jsonify(user.to_dict())


@auth_bp.route("/users/<int:user_id>", methods=["PATCH"])
@admin_token_required
def update_user_patch(user_id):
    data = request.get_json(silent=True) or {}

    if "name" not in data and "email" not in data:
        return jsonify({"error": "Name and/or Email must be provided"}), 400

    name = data["name"].strip() if "name" in data else None
    email = data["email"].strip() if "email" in data else None

    if name is not None and not name:
        return jsonify({"error": "The Name field cannot be empty"}), 400

    if email is not None and not email:
        return jsonify({"error": "The Email field cannot be empty"}), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User Not Found"}), 404

    if name is not None:
        user.name = name

    if email is not None:
        user.email = email

    db.session.commit()
    return jsonify(user.to_dict())


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_token_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User Not Found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User Removed"}), 200
