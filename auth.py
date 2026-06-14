from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from base_data import *
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']

            if user['name'] == 'Admin':
                return redirect(url_for('auth.profile_admin'))
            else:
                return redirect(url_for('auth.profile'))
        else:
            flash('Invalid email or password')
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = get_db()
        try:
            conn.execute('INSERT INTO users(name, phone, email, password) VALUES(?,?,?,?)',
                         (name, phone, email, password))
            conn.commit()
            flash('Thank you for registering. Please login.')
            return redirect(url_for('auth.login'))
        except:
            flash('This user already exists.')
        finally:
            conn.close()
    return render_template('register.html')


@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('profile.html', name=session['user_name'])

@auth_bp.route('/profileadmin')
def profile_admin():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('profileadmin.html', name=session['user_name'])

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))