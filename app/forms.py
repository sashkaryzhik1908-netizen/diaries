from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    IntegerField,
    TextAreaField,
    SubmitField,
    SelectField,
    BooleanField,
    PasswordField,
)

from wtforms.validators import DataRequired, EqualTo


# Формы
class RegisterForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(),
            EqualTo("confirm", message="Пароли должны совпадать"),
        ],
    )
    confirm = PasswordField(
        "Подтвердите пароль",
        validators=[DataRequired()],
    )
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired()],
    )
    submit = SubmitField("Войти")


class CategoryForm(FlaskForm):
    name = StringField(
        "Введите название категории",
        validators=[DataRequired()],
    )
    slug = StringField(
        "Введите техническое название категории",
        validators=[DataRequired()],
    )
    template = TextAreaField(
        "Шаблон категории",
        validators=[DataRequired()],
    )
    submit = SubmitField("Сохранить изменения")


class TemplateVariableForm(FlaskForm):
    name = StringField(
        "Техническое имя",
        validators=[DataRequired()],
    )
    label = StringField(
        "Название поля",
        validators=[DataRequired()],
    )
    field_type = SelectField(
        "Тип поля",
        choices=[
            ("select", "Один вариант"),
            ("multiselect", "Несколько вариантов"),
            ("text", "Текст"),
            ("number", "Число"),
            ("date", "Дата"),
        ],
    )
    required = BooleanField("Обязательное поле")
    submit = SubmitField("Сохранить")


class VariableOptionForm(FlaskForm):
    value = StringField(
        "Значение",
        validators=[DataRequired()],
    )
    output_value = StringField(
        "Выводимое значение",
        validators=[DataRequired()],
    )
    order = IntegerField(
        "Порядок отображения",
        validators=[DataRequired()],
    )
    submit = SubmitField("Сохранить")


class TherapyPurposeForm(FlaskForm):
    name = StringField(
        "Название цели терапии",
        validators=[DataRequired()],
    )
    output_value = StringField(
        "Отображаемое значение",
        validators=[DataRequired()],
    )
    order = IntegerField(
        "Порядок отображения",
        validators=[DataRequired()],
    )
    submit = SubmitField("Сохранить")


class TherapyMedicationForm(FlaskForm):
    name = StringField(
        "Название препарата",
        validators=[DataRequired()],
    )
    submit = SubmitField("Сохранить")
