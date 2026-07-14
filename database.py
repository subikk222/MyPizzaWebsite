from sqlalchemy import inspect, text

from models import Product, User, db

DEFAULT_PRODUCTS = [
    {
        "name": "Маргарита",
        "price": 150,
        "description": "Класична піца з томатами та сиром моцарела.",
        "image_url": "https://pics.craiyon.com/2023-05-22/b6dee723d68d461c891cc552095529cb.webp",
    },
    {
        "name": "Пепероні",
        "price": 220,
        "description": "Піца з пікантною ковбаскою пепероні та сиром.",
        "image_url": "https://tse4.mm.bing.net/th/id/OIP.tDgGf_psZbO2DOO6ZaSe_AHaE7?pid=Api&P=0&h=180",
    },
    {
        "name": "Гавайська",
        "price": 200,
        "description": "Курка, ананас та сир — незвичне поєднання.",
        "image_url": "https://thumbs.dreamstime.com/b/pineapple-hawaiian-pizza-chicken-pineapple-cut-pieces-white-background-isolate-pineapple-hawaiian-pizza-261782984.jpg",
    },
    {
        "name": "4 Сири",
        "price": 150,
        "description": "Моцарела, дорблю, пармезан і чедер.",
        "image_url": "https://static.vecteezy.com/system/resources/previews/056/914/536/non_2x/delicious-4-cheese-pizza-isolated-on-transparent-background-melted-mozzarella-parmesan-gorgonzola-and-ricotta-italian-cuisine-cheesy-appetizing-png.png",
    },
    {
        "name": "Мʼясна",
        "price": 320,
        "description": "Бекон, шинка, ковбаски та сир.",
        "image_url": "https://tse1.mm.bing.net/th/id/OIP.Ty8YcY7ijZEOCB4RKW5S2QHaHa?pid=Api&P=0&h=180",
    },
    {
        "name": "Овочева",
        "price": 400,
        "description": "Свіжі овочі, маслини та томатний соус.",
        "image_url": "https://tse4.mm.bing.net/th/id/OIP.K6tQaLvFU5tGCALQaRFhrgHaHa?pid=Api&P=0&h=180",
    },
]


def _migrate_users_role():
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "role" not in columns:
        db.session.execute(
            text("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        )
        db.session.commit()

    db.session.execute(
        text("UPDATE users SET role = 'admin' WHERE name = 'Admin'")
    )
    db.session.commit()


def seed_products():
    if Product.query.count() > 0:
        return

    db.session.add_all([Product(**product) for product in DEFAULT_PRODUCTS])
    db.session.commit()


def init_db():
    db.create_all()
    _migrate_users_role()
    seed_products()