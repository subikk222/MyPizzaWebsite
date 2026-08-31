from flask import Blueprint, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from models import User, db
import jwt
import logging
from functools import wraps


auth_bp = Blueprint("auth", __name__)
logging.basicConfig(level=logging.INFO)

SECRET_KEY = "jwt-secret-key"
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60

def create_token(username, role):
    payload = {
        "sub": username,
        "role": role,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            auth_bp.logger.info("[JWT] protected route called without Bearer token")
            return jsonify({"error": "Authorization: Bearer <token> required"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            auth_bp.logger.info("[JWT] token expired")
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            auth_bp.logger.info("[JWT] invalid token")
            return jsonify({"error": "Invalid token"}), 401

        request.user = payload
        return f(*args, **kwargs)

    return decorated






def _current_user():
    if "user_id" not in session:
        return None
    return db.session.get(User, session["user_id"])


# --- Web: login, registration, profile ---


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user:
            if user.role == "admin":
                valid = bcrypt.checkpw(
                    password.encode("utf-8"),
                    user.password.encode("utf-8")
                )
            else:
                valid = check_password_hash(user.password, password)

            if valid:
                session["user_id"] = user.id
                session["user_name"] = user.name
                session["user_role"] = user.role

                if user.role == "admin":
                    return redirect(url_for("auth.profile_admin"))

                return redirect(url_for("auth.profile"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        password_text = request.form["password"]
        admin_code = request.form.get("admin_code")

        if admin_code == "pizza_admin":
            role = "admin"

            password = bcrypt.hashpw(
                password_text.encode("utf-8"),
                bcrypt.gensalt()
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
def profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    return render_template("profile.html", user=user)


@auth_bp.route("/profileadmin")
def profile_admin():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, session["user_id"])
    if not user or user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("shop.index"))

    return render_template("profileadmin.html", name=session["user_name"])


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("shop.index"))


@auth_bp.route("/reset_name", methods=["POST"])
def reset_name():
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login"))

    new_name = (request.form.get("new_name") or "").strip()
    if not new_name:
        flash("The Name can't be empty.", "danger")
        return redirect(url_for("auth.profile"))

    user.name = new_name
    session["user_name"] = new_name
    db.session.commit()
    flash("The Name is successfully updated.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/reset_number", methods=["POST"])
def reset_number():
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login"))

    new_number = (request.form.get("new_number") or "").strip()
    if not new_number.isdigit():
        flash("The Phone Number can't be empty.", "danger")
        return redirect(url_for("auth.profile"))

    user.phone = new_number
    db.session.commit()
    flash("The Phone Number is successfully updated.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/reset_email", methods=["POST"])
def reset_email():
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login"))

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
def reset_password():
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login"))

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


# --- JSON: CRUD users (Postman, beginner task) ---


@auth_bp.route("/users", methods=["GET"])
def get_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([user.to_dict() for user in users])


@auth_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    password = (data.get("password") or "").strip()

    if not name or not email:
        return jsonify({"error": "The Name and Price fields are require"}), 400

    user = User(name=name, email=email, phone=phone, password=password)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@auth_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User Not Found"}), 404

    return jsonify(user.to_dict())


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user_put(user_id):
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not email:
        return jsonify({"error": "The Name and Price fields are required"}), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User Not Found"}), 404

    user.name = name
    user.email = email
    db.session.commit()

    return jsonify(user.to_dict())


@auth_bp.route("/users/<int:user_id>", methods=["PATCH"])
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
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User Not Found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User Removed"}), 200
