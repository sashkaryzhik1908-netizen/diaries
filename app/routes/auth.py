from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required,
)

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager
from app.models import User, Diary
from app.forms import RegisterForm, LoginForm, EditUserForm

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


# Редактирование профиля
@auth_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_user():
    user = current_user
    form = EditUserForm(obj=user)

    if form.validate_on_submit():

        # Проверяем, занят ли логин другим пользователем
        existing_user = User.query.filter_by(
            username=form.username.data
        ).first()

        if existing_user and existing_user.id != user.id:
            flash("Это имя пользователя уже занято.", "danger")
            return render_template("auth/edit_user.html", form=form)

        user.username = form.username.data

        # Если введён новый пароль, обновляем его
        if form.password.data:
            user.password = generate_password_hash(form.password.data)

        db.session.commit()

        flash("Данные профиля успешно обновлены.", "success")
        return redirect(url_for("auth.user"))

    return render_template("auth/edit_user.html", form=form)


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


@auth_bp.route("/user")
@login_required
def user():
    diaries = Diary.query.filter(Diary.user_id == current_user.id).all()
    return render_template(
        "auth/user.html",
        user=current_user,
        diaries=diaries)
