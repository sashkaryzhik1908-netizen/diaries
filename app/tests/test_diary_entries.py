import json

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Category, Diary, DiaryEntry, TemplateVariable, User


# Создание тестового пользователя
def create_user(username):
    user = User(
        username=username,
        password=generate_password_hash("123456"),
        is_admin=False,
    )

    db.session.add(user)
    db.session.commit()

    return user


# Вход пользователя
def login(client, username):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": "123456",
        },
    )


# Создание тестового дневника и категории
def create_diary_with_category(username):
    user = create_user(username)

    diary = Diary(
        user_id=user.id,
        number=1,
    )

    category = Category(
        name="Жалобы",
        slug="complaints",
        order=1,
        template="Жалобы: {{ complaints }}",
    )

    db.session.add_all([diary, category])
    db.session.commit()

    variable = TemplateVariable(
        category_id=category.id,
        name="complaints",
        label="Жалобы",
        field_type="text",
        required=True,
    )

    db.session.add(variable)
    db.session.commit()

    return diary, category


# Проверка открытия формы заполнения категории
def test_fill_category_page(client, app):
    with app.app_context():
        diary, category = create_diary_with_category("user1")

        diary_id = diary.id
        category_id = category.id

    login(client, "user1")

    response = client.get(f"/diaries/{diary_id}/categories/{category_id}/fill")

    assert response.status_code == 200


# Проверка сохранения новой записи дневника
def test_save_category_entry(client, app):
    with app.app_context():
        diary, category = create_diary_with_category("user1")

        diary_id = diary.id
        category_id = category.id

    login(client, "user1")

    response = client.post(
        f"/diaries/{diary_id}/categories/{category_id}/fill",
        data={
            "complaints": "Головная боль",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        entry = DiaryEntry.query.filter_by(
            diary_id=diary_id,
            category_id=category_id,
        ).first()

        assert entry is not None
        assert entry.text == "Жалобы: Головная боль"
        assert entry.position == 0


# Проверка обновления существующей записи
def test_update_category_entry(client, app):
    with app.app_context():
        diary, category = create_diary_with_category("user1")

        diary_id = diary.id
        category_id = category.id

    login(client, "user1")

    url = f"/diaries/{diary_id}/categories/{category_id}/fill"

    # Первое сохранение
    client.post(
        url,
        data={
            "complaints": "Головная боль",
        },
    )

    # Повторное сохранение
    response = client.post(
        url,
        data={
            "complaints": "Боль в животе",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        entries = DiaryEntry.query.filter_by(
            diary_id=diary_id,
            category_id=category_id,
        ).all()

        assert len(entries) == 1
        assert entries[0].text == "Жалобы: Боль в животе"


# Проверка сохранения данных формы
def test_save_category_form_data(client, app):
    with app.app_context():
        diary, category = create_diary_with_category("user1")

        diary_id = diary.id
        category_id = category.id

    login(client, "user1")

    client.post(
        f"/diaries/{diary_id}/categories/{category_id}/fill",
        data={
            "complaints": "Головная боль",
        },
    )

    with app.app_context():
        entry = DiaryEntry.query.filter_by(
            diary_id=diary_id,
            category_id=category_id,
        ).first()

        form_data = json.loads(entry.form_data)

        assert form_data == {
            "complaints": ["Головная боль"],
        }


# Проверка восстановления ранее сохранённых данных формы
def test_restore_category_form_data(client, app):
    with app.app_context():
        diary, category = create_diary_with_category("user1")

        diary_id = diary.id
        category_id = category.id

        entry = DiaryEntry(
            diary_id=diary_id,
            category_id=category_id,
            text="Жалобы: Головная боль",
            position=0,
            syndromes="",
            form_data=json.dumps(
                {
                    "complaints": ["Головная боль"],
                },
                ensure_ascii=False,
            ),
        )

        db.session.add(entry)
        db.session.commit()

    login(client, "user1")

    response = client.get(f"/diaries/{diary_id}/categories/{category_id}/fill")

    assert response.status_code == 200
    assert "Головная боль".encode() in response.data


# Проверка обязательного поля
def test_fill_category_required_field(client, app):
    with app.app_context():
        diary, category = create_diary_with_category("user1")

        diary_id = diary.id
        category_id = category.id

    login(client, "user1")

    response = client.post(
        f"/diaries/{diary_id}/categories/{category_id}/fill",
        data={
            "complaints": "",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        entry = DiaryEntry.query.filter_by(
            diary_id=diary_id,
            category_id=category_id,
        ).first()

        assert entry is None


# Проверка запрета доступа к чужому дневнику
def test_user_cannot_fill_another_users_diary(client, app):
    with app.app_context():
        # Создаём владельца дневника
        diary, category = create_diary_with_category("user2")

        # Создаём другого пользователя
        create_user("user1")

        diary_id = diary.id
        category_id = category.id

    # Входим под другим пользователем
    login(client, "user1")

    response = client.get(f"/diaries/{diary_id}/categories/{category_id}/fill")

    assert response.status_code == 404


# Проверка обработки повреждённых данных формы
def test_restore_invalid_category_form_data(client, app):
    with app.app_context():
        diary, category = create_diary_with_category("user1")

        diary_id = diary.id
        category_id = category.id

        entry = DiaryEntry(
            diary_id=diary_id,
            category_id=category_id,
            text="Жалобы: Головная боль",
            position=0,
            syndromes="",
            form_data="{invalid json",
        )

        db.session.add(entry)
        db.session.commit()

    login(client, "user1")

    response = client.get(f"/diaries/{diary_id}/categories/{category_id}/fill")

    assert response.status_code == 200


# Проверка открытия формы назначений
def test_fill_prescriptions_category(client, app):
    with app.app_context():
        user = create_user("user1")

        diary = Diary(
            user_id=user.id,
            number=1,
        )

        category = Category(
            name="Назначения",
            slug="prescriptions",
            order=1,
            template="",
        )

        db.session.add_all([diary, category])
        db.session.commit()

        diary_id = diary.id
        category_id = category.id

    login(client, "user1")

    response = client.get(f"/diaries/{diary_id}/categories/{category_id}/fill")

    assert response.status_code == 200


# Проверка обработки ошибки при сохранении записи
def test_save_category_entry_commit_error(client, app, monkeypatch):
    with app.app_context():
        diary, category = create_diary_with_category("user1")

        diary_id = diary.id
        category_id = category.id

    login(client, "user1")

    def fail_commit():
        raise RuntimeError("Ошибка тестового сохранения")

    monkeypatch.setattr(db.session, "commit", fail_commit)

    response = client.post(
        f"/diaries/{diary_id}/categories/{category_id}/fill",
        data={
            "complaints": "Головная боль",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        entry = DiaryEntry.query.filter_by(
            diary_id=diary_id,
            category_id=category_id,
        ).first()

        assert entry is None
