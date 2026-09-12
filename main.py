from flask import Flask
import stripe
from config import Config
from database import init_db
from models import db
from routes.auth import auth_bp
from routes.cart import cart_bp
from routes.reviews import reviews_bp
from routes.shop import shop_bp
from routes.admin_orders import admin_orders_bp
from routes.admin_users import admin_users_bp
from routes.user_orders import user_orders_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    stripe.api_key = app.config["STRIPE_SECRET_KEY"]

    @app.context_processor
    def inject_auth_user():
        """Templates: current_user замість session.user_*."""
        from auth_jwt import get_current_user

        return {"current_user": get_current_user()}

    app.register_blueprint(shop_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(admin_orders_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(user_orders_bp)

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=app.config["DEBUG"])