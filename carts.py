from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from base_data import *
import stripe

carts_bp = Blueprint('carts', __name__)


@carts_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    cart = session.get('cart', [])

    if not cart:
        return redirect(url_for('carts.cart'))

    line_items = []

    for item in cart:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item['name'],
                },
                'unit_amount': int(item['price'] * 100),
            },
            'quantity': item['qty'],
        })

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=url_for('carts.success', _external=True),
        cancel_url=url_for('carts.cancel', _external=True),
    )

    return redirect(checkout_session.url)


@carts_bp.route('/cancel')
def cancel():
    return render_template("cancel.html")


@carts_bp.route('/success')
def success():
    session.pop('cart', None)
    return render_template("success.html")


@carts_bp.route('/add_cart/<int:pizza_id>', methods=['POST'])
def add_cart(pizza_id):
    quantity = int(request.form.get('quantity', 1))
    pizza = PIZZAS.get(pizza_id)

    if not pizza:
        flash('Invalid pizza id')
        return redirect(url_for('index'))

    if 'cart' not in session:
        session['cart'] = []

    for item in session['cart']:
        if item['id'] == pizza_id:
            item['qty'] += quantity
            session.modified = True
            return redirect(url_for('carts.cart'))

    session['cart'].append({
        "id": pizza_id,
        "name": pizza["name"],
        "price": pizza["price"],
        "qty": quantity
    })

    session.modified = True

    return redirect(url_for('index'))


@carts_bp.route('/update_quantity/<int:index>/<string:action>', methods=['POST'])
def update_quantity(index, action):

    if 'cart' in session and 0 <= index < len(session['cart']):

        if action == 'plus':
            session['cart'][index]['qty'] += 1

        elif action == 'minus':
            session['cart'][index]['qty'] -= 1

            if session['cart'][index]['qty'] <= 0:
                session['cart'].pop(index)

        session.modified = True

    return redirect(url_for('carts.cart'))


@carts_bp.route('/cart')
def cart():

    cart = session.get('cart', [])

    for item in cart:
        if 'qty' not in item:
            item['qty'] = 1

    session.modified = True

    total = sum(item['price'] * item['qty'] for item in cart)

    return render_template("cart.html", cart=cart, total=total)