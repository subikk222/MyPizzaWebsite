from flask import Flask, Blueprint, jsonify, render_template, request
from models import User, db


edit_bp = Blueprint("edit", __name__)



@edit_bp.route('/editpayment', methods=['GET', 'POST'])
def edit():

    return render_template("edit.html")