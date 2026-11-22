from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager
from app.forms import EditUserForm, LoginForm, RegisterForm
from app.models import Diary, User

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

        existing_user = db.session.scalar(select(User).where(User.username == username))

        if existing_user:
            flash("Такое имя пользователя уже занято.", "warning")
            return render_template("auth/register.html", form=form)

        user = User(
            username=username,
            password=generate_password_hash(password),
        )

        db.session.add(user)
        db.session.commit()

        login_user(user)

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
        existing_user = db.session.scalar(
            select(User).where(User.username == form.username.data)
        )

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

@auth_bp.route("/delete", methods=["POST"])
@login_required
def del_user():
    user = current_user._get_current_object()

    logout_user()

    db.session.delete(user)
    db.session.commit()

    flash("Профиль удален", "success")
    return redirect(url_for("auth.index"))



# Вход
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = db.session.scalar(select(User).where(User.username == username))

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
    diaries = db.session.scalars(
        select(Diary).where(Diary.user_id == current_user.id)
    ).all()
    return render_template("auth/user.html", user=current_user, diaries=diaries)
