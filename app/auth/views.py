from flask import (
    Response,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from sqlite3 import IntegrityError
from wtforms import ValidationError

from . import auth
from ..forms.signin import SigninForm
from ..forms.login import LoginForm
from app import db, bcrypt, login_user, logout_user
from models.model import Users


# =========================
# SIGNIN (REGISTER LOGIC)
# =========================
@auth.route('/signin', methods=["GET", "POST"])
def signin() -> (Response | str):

    form = SigninForm()

    if form.validate_on_submit():

        existing_admin = Users.query.filter_by(is_admin=True).first()

        try:
            # FIRST USER = ADMIN
            if not existing_admin:

                Users.create_admin(
                    username=form.username.data,
                    email=form.email.data,
                    password1=form.password1.data
                )

                user = Users.query.filter_by(email=form.email.data).first()
                login_user(user)

                flash("Admin account created successfully 🚀", "success")
                return redirect(url_for("market.market_home"))

            # NORMAL USER
            Users.create_user(
                username=form.username.data,
                email=form.email.data,
                password1=form.password1.data
            )

            user = Users.query.filter_by(email=form.email.data).first()
            login_user(user)

            flash(f"Welcome {user.username} 🎉", "success")
            return redirect(url_for("market.market_home"))

        except IntegrityError:
            db.session.rollback()
            flash("Email already exists ❌", "danger")

        except ValidationError as e:
            flash("Validation error: " + " ".join(e.messages), "danger")

    return render_template("auth/signin.html", form=form)


# =========================
# LOGIN
# =========================
@auth.route('/login', methods=["GET", "POST"])
def login() -> (Response | str):

    form = LoginForm()

    if form.validate_on_submit():

        user = Users.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):

            login_user(user)
            flash("Login successful 🚀", "success")
            return redirect(url_for("market.market_home"))

        flash("Invalid email or password ❌", "danger")

    return render_template("auth/login.html", form=form)


# =========================
# LOGOUT
# =========================
@auth.route('/logout')
def logout() -> Response:

    logout_user()
    flash("You have been logged out 👋", "info")

    return redirect(url_for("main.home"))