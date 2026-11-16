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

from wtforms.validators import (
    DataRequired,
    EqualTo,
    Length,
    InputRequired,
    NumberRange,
)


# Формы
class RegisterForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
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
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired()],
    )
    submit = SubmitField("Войти")


class CategoryForm(FlaskForm):
    name = StringField(
        "Введите название категории",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    slug = StringField(
        "Введите техническое название категории",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    template = TextAreaField(
        "Шаблон категории",
        validators=[DataRequired()],
    )
    submit = SubmitField("Сохранить изменения")


class TemplateVariableForm(FlaskForm):
    name = StringField(
        "Техническое имя",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    label = StringField(
        "Название поля",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
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
        validators=[DataRequired()],
    )
    required = BooleanField("Обязательное поле")
    submit = SubmitField("Сохранить")


class VariableOptionForm(FlaskForm):
    value = StringField(
        "Значение",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )
    output_value = StringField(
        "Выводимое значение",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )
    order = IntegerField(
        "Порядок отображения",
        validators=[
            InputRequired(),
            NumberRange(min=0),
        ],
    )
    submit = SubmitField("Сохранить")


class TherapyPurposeForm(FlaskForm):
    name = StringField(
        "Название цели терапии",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
    )
    output_value = StringField(
        "Отображаемое значение",
        validators=[
            DataRequired(),
            Length(max=200),
        ],
    )
    order = IntegerField(
        "Порядок отображения",
        validators=[
            InputRequired(),
            NumberRange(min=0),
        ],
    )
    submit = SubmitField("Сохранить")


class TherapyMedicationForm(FlaskForm):
    name = StringField(
        "Название препарата",
        validators=[
            DataRequired(),
            Length(max=200),
        ],
    )
    submit = SubmitField("Сохранить")
