from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required,
)

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager
from app.models import User
from app.forms import RegisterForm, LoginForm


auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Регистрация
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Такое имя пользователя уже занято.", "warning")
            return render_template("auth/register.html", form=form)

        user = User(
            username=username,
            password=generate_password_hash(password),
        )

        db.session.add(user)
        db.session.commit()

        flash("Регистрация успешно завершена.", "success")
        return redirect(url_for("auth.index"))

    return render_template("auth/register.html", form=form)


# Вход
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Вы успешно вошли в систему.", "success")
            return redirect(url_for("auth.index"))

        flash("Неверное имя пользователя или пароль.", "danger")

    return render_template("auth/login.html", form=form)


# Выход
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.index"))


# Главная страница
@auth_bp.route("/")
def index():
    return render_template("index.html")
