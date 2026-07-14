from flask import Blueprint, render_template, request, redirect, url_for

from models import Review, db

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("/score", methods=["GET", "POST"])
def score():
    if request.method == "POST":
        review = Review(
            name=request.form["name"],
            email=request.form["email"],
            rating=request.form["rating"],
            feedback=request.form["feedback"],
        )
        db.session.add(review)
        db.session.commit()
        return redirect(url_for("reviews.thankyou"))
    return render_template("score.html")


@reviews_bp.route("/thankyou")
def thankyou():
    return render_template("thank.html")
