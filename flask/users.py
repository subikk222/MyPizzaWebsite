from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
USE_SQLALCHEMY = False
try:
    from models import User, db

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    USE_SQLALCHEMY = True
except ImportError:
    import database_sqlite as storage

def seed_database():
    if User.query.count() > 0:
        return

    samples = [

        User(name="Admin", email="admin@gmail.com"),
    ]
    db.session.add_all(samples)
    db.session.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([user.to_dict() for user in users])

#-----------------------------------------

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not email:
        return jsonify({"error": "Поля user та email обовʼязкові"}), 400

    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201

#-----------------------------------------

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    if USE_SQLALCHEMY:
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"error": "Юзер не знайдено"}), 404


    db.session.commit()
    return jsonify(({"message": "Юзер знайдено"}))

#-----------------------------------------

@app.route("/users/<int:user_id>", methods=["PUT"])
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

#-----------------------------------------

@app.route("/users/<int:user_id>", methods=["PATCH"])
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

#-----------------------------------------

@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Юзер не знайдено"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Юзери видалено"})

#-----------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_database()

    app.run(debug=True)
