from flask import Blueprint, jsonify, render_template, request

from models import Product, db

shop_bp = Blueprint("shop", __name__)


# --- Веб: каталог піц ---


@shop_bp.route("/")
def index():
    products = Product.query.order_by(Product.id.asc()).all()
    return render_template("index.html", products=products)


# --- JSON: CRUD продуктів (Postman, навчальні завдання) ---


@shop_bp.route("/products", methods=["GET"])
def get_products():
    products = Product.query.order_by(Product.id.asc()).all()
    return jsonify([product.to_dict() for product in products])


@shop_bp.route("/products", methods=["POST"])
def create_product():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    price = data.get("price")
    description = (data.get("description") or "").strip()
    image_url = (data.get("image_url") or "").strip()

    if not name or price in (None, ""):
        return jsonify({"error": "Поля name та price обов'язкові"}), 400

    product = Product(
        name=name,
        price=float(price),
        description=description,
        image_url=image_url,
    )
    db.session.add(product)
    db.session.commit()

    return jsonify(product.to_dict()), 201


@shop_bp.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "Продукт не знайдено"}), 404

    return jsonify(product.to_dict())


@shop_bp.route("/products/<int:product_id>", methods=["PUT"])
def update_product_put(product_id):
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    price = data.get("price")

    if not name or price in (None, ""):
        return jsonify({"error": "Поля name та price обовʼязкові"}), 400

    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "Продукт не знайдено"}), 404

    product.name = name
    product.price = float(price)
    db.session.commit()

    return jsonify(product.to_dict())


@shop_bp.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "Продукт не знайдено"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Продукт видалено"})
