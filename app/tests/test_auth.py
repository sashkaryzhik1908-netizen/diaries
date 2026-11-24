import pytest
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User


# Проверка главной страницы
def test_index_page(client):
    response = client.get("/")

    assert response.status_code == 200


# Проверка страницы регистрации
def test_register_page(client):
    response = client.get("/register")

    assert response.status_code == 200


# Проверка регистрации пользователя
def test_register_user(client, app):
    response = client.post(
        "/register",
        data={
            "username": "test_user",
            "name": "Test User",
            "password": "123456",
            "confirm": "123456",
            "submit": "Зарегистрироваться",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="test_user").first()

        assert user is not None
        assert user.is_admin is False


# Проверка входа
def test_login_user(client, app):
    with app.app_context():
        user = User(
            username="login_user",
            password=generate_password_hash("123456"),
            is_admin=False,
        )

        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={
            "username": "login_user",
            "password": "123456",
            "submit": "Войти",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Вы успешно вошли в систему.".encode() in response.data


# Проверка выхода
def test_logout_user(client, app):
    with app.app_context():
        user = User(
            username="logout_user",
            password=generate_password_hash("123456"),
            is_admin=False,
        )

        db.session.add(user)
        db.session.commit()

    client.post(
        "/login",
        data={
            "username": "logout_user",
            "password": "123456",
        },
    )

    response = client.post("/logout", follow_redirects=True)

    assert response.status_code == 200
    assert "Вы вышли из системы.".encode() in response.data


# Создание пользователя и вход в систему
def create_and_login_user(client, app, username, is_admin):
    with app.app_context():
        user = User(
            username=username,
            password=generate_password_hash("123456"),
            is_admin=is_admin,
        )

        db.session.add(user)
        db.session.commit()

    return client.post(
        "/login",
        data={
            "username": username,
            "password": "123456",
        },
        follow_redirects=True,
    )


# Проверка доступа обычного пользователя к административным страницам
@pytest.mark.parametrize(
    "url",
    [
        "/categories",
        "/therapy/purposes",
        "/therapy/medications",
        "/laboratory/categories",
    ],
)
def test_regular_user_cannot_access_admin_pages(client, app, url):
    create_and_login_user(
        client,
        app,
        username="regular_user",
        is_admin=False,
    )

    response = client.get(url)

    assert response.status_code == 403


# Проверка доступа администратора к административным страницам
@pytest.mark.parametrize(
    "url",
    [
        "/categories",
        "/therapy/purposes",
        "/therapy/medications",
        "/laboratory/categories",
    ],
)
def test_admin_can_access_admin_pages(client, app, url):
    create_and_login_user(
        client,
        app,
        username="admin_user",
        is_admin=True,
    )

    response = client.get(url)

    assert response.status_code == 200


# Проверка карточек главной страницы для обычного пользователя
def test_regular_user_sees_only_diaries_card(client, app):
    create_and_login_user(
        client,
        app,
        username="index_regular",
        is_admin=False,
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Медицинские дневники".encode() in response.data
    assert "Лаборатория".encode() not in response.data
    assert "Препараты".encode() not in response.data
    assert "Шаблоны".encode() not in response.data


# Проверка карточек главной страницы для администратора
def test_admin_sees_all_cards(client, app):
    create_and_login_user(
        client,
        app,
        username="index_admin",
        is_admin=True,
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Медицинские дневники".encode() in response.data
    assert "Лаборатория".encode() in response.data
    assert "Терапия".encode() in response.data
    assert "Препараты".encode() in response.data
    assert "Шаблоны".encode() in response.data
