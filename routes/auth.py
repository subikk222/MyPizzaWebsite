

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from models import User, db

auth_bp = Blueprint("auth", __name__)


def _current_user():
    if "user_id" not in session:
        return None
    return db.session.get(User, session["user_id"])


# --- Веб: логін, реєстрація, профіль ---


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

        if User.query.filter_by(email=email).first():
            flash("This user already exists.", "danger")
            return render_template("register.html")

        user = User(name=name, phone=phone, email=email, password=password)
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
        flash("Імʼя не може бути порожнім.", "danger")
        return redirect(url_for("auth.profile"))

    user.name = new_name
    session["user_name"] = new_name
    db.session.commit()
    flash("Імʼя успішно оновлено.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/reset_number", methods=["POST"])
def reset_number():
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login"))

    new_number = (request.form.get("new_number") or "").strip()
    if not new_number.isdigit():
        flash("Номер телефону не може бути порожнім.", "danger")
        return redirect(url_for("auth.profile"))

    user.phone = new_number
    db.session.commit()
    flash("Номер телефону успішно оновлено.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/reset_email", methods=["POST"])
def reset_email():
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login"))

    new_email = (request.form.get("new_email") or "").strip().lower()
    if not new_email or "@" not in new_email:
        flash("Введіть коректний email.", "danger")
        return redirect(url_for("auth.profile"))

    existing = User.query.filter_by(email=new_email).first()
    if existing and existing.id != user.id:
        flash("Цей email уже використовується іншим акаунтом.", "danger")
        return redirect(url_for("auth.profile"))

    user.email = new_email
    db.session.commit()
    flash("Email успішно оновлено.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/reset_password", methods=["POST"])
def reset_password():
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login"))

    new_password = request.form.get("new_password") or ""
    if len(new_password) < 6:
        flash("Пароль має містити щонайменше 6 символів.", "danger")
        return redirect(url_for("auth.profile"))

    if user.role == "admin":
        user.password = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
    else:
        user.password = generate_password_hash(new_password)

    db.session.commit()
    flash("Пароль успішно оновлено.", "success")
    return redirect(url_for("auth.profile"))


# --- JSON: CRUD користувачів (Postman, навчальні завдання) ---


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
        return jsonify({"error": "Поля name та email обовʼязкові"}), 400

    user = User(name=name, email=email, phone=phone, password=password)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@auth_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Юзер не знайдено"}), 404

    return jsonify(user.to_dict())


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user_put(user_id):
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not email:
        return jsonify({"error": "Поля name та email обовʼязкові"}), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Юзера не знайдено"}), 404

    user.name = name
    user.email = email
    db.session.commit()

    return jsonify(user.to_dict())


@auth_bp.route("/users/<int:user_id>", methods=["PATCH"])
def update_user_patch(user_id):
    data = request.get_json(silent=True) or {}

    if "name" not in data and "email" not in data:
        return jsonify({"error": "Потрібно передати name і/або email"}), 400

    name = data["name"].strip() if "name" in data else None
    email = data["email"].strip() if "email" in data else None

    if name is not None and not name:
        return jsonify({"error": "Поле name не може бути порожнім"}), 400

    if email is not None and not email:
        return jsonify({"error": "Поле email не може бути порожнім"}), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Юзера не знайдено"}), 404

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
        return jsonify({"error": "Юзер не знайдено"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Юзера видалено"})
