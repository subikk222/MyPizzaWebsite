from flask import Flask
app = Flask(__name__)

@app.route('/editpayment', methods=['GET', 'POST'])
def edit():
    return edit("profileadmin.html")