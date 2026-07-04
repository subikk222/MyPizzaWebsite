from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
USE_SQLALCHEMY = False
try:
    from models import Product, db

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    USE_SQLALCHEMY = True
except ImportError:
    import database_sqlite as storage

def seed_database():
    if Product.query.count() > 0:
        return

    samples = [

        Product(name="Pizza Margarita", price=20.0)

    ]
    db.session.add_all(samples)
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

#--------------------------------------------------

@app.route('/products', methods=['GET'])
def get_products():
    if USE_SQLALCHEMY:
        products = Product.query.order_by(Product.id.desc()).all()
        return jsonify([product.to_dict() for product in products])
    return jsonify(storage.get_all())

#--------------------------------------------------

@app.route('/products', methods = ['POST'])
def create_product():
    data = request.get_json(silent=True)

    name = (data.get('name') or "").strip()
    price = (data.get('price') or "")

    if not name or not price:
        return jsonify({"error": "Поля name та price обов'язкові"}), 400

    product = Product(name=name, price=price)
    db.session.add(product)
    db.session.commit()

    return jsonify(product.to_dict()), 201

#--------------------------------------------------

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    if USE_SQLALCHEMY:
        product = Product.query.get(product_id)
        if product is None:
            return jsonify({"error":"Продукт не знайдено"}), 404

    db.session.commit()
    return jsonify({"message": "Продукт знайдено"})

#--------------------------------------------------

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product_put(product_id):
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    price = (data.get("price") or "")

    if not name or not price:
        return jsonify({"error": "Поля name та price обовʼязкові"}), 400
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "Юзера не знайдено"}), 404

    product.name = name
    product.price = price
    db.session.commit()

    return jsonify(product.to_dict())

#--------------------------------------------------

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    if USE_SQLALCHEMY:
        product = db.session.get(Product, product_id)
        if product is None:
            return jsonify({"error": "Продукт не знайдено"}), 404

        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Продукт видалено"})

    if not storage.delete_product(product_id):
        return jsonify({"error": "Продукт не знайдено"}), 404

    return jsonify({"message": "Продукт Видалено"})

#-----------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_database()

    app.run(debug=True)
