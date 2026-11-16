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
            password="scrypt:32768:8:1$test$salt",
            is_admin=False,
        )

        from werkzeug.security import generate_password_hash

        user.password = generate_password_hash("123456")

        from app.extensions import db

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
    from werkzeug.security import generate_password_hash
    from app.extensions import db

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
