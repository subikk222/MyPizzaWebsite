from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from base_data import *
from carts import carts_bp
from auth import auth_bp

import stripe
import json

with open("C:\\Users\\stas1\\PycharmProjects\\PythonProjectWeb\\templates\\keys.json", "r", encoding="utf-8") as file: data = json.load(file)

stripe.api_key = data["stripe"]

app = Flask(__name__)
app.secret_key = 'qwerty'

app.register_blueprint(carts_bp)
app.register_blueprint(auth_bp)

@app.route('/score', methods=['GET', 'POST'])
def score():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        rating = request.form['rating']
        feedback = request.form['feedback']

        conn = get_db()
        conn.execute('INSERT INTO base(name, email, rating, feedback) VALUES (?, ?, ?, ?)',
                     (name, email, rating, feedback))
        conn.commit()
        conn.close()
        return redirect(url_for('thankyou'))
    return render_template('score.html')
@app.route('/thankyou')
def thankyou():
    return render_template('thank.html')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    create_table()
    create_user()
    app.run(debug=True)


