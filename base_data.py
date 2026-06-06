import sqlite3

def get_db():
    conn = sqlite3.connect('base.db')
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        rating INTEGER NOT NULL,
        feedback TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def create_user():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
        )

    ''')
    conn.commit()
    conn.close()


PIZZAS = {
    1: {'name': 'Маргарита', 'price': 150},
    2: {'name': 'Пепероні', 'price': 220},
    3: {'name': 'Гавайська', 'price': 200},
    4: {'name': '4 Сири', 'price': 150},
    5: {'name': 'Мʼясна', 'price': 320},
    6: {'name': 'Овочева', 'price': 400}
}