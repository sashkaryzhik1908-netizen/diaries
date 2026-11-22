from datetime import UTC, datetime

from flask_login import UserMixin

from app.extensions import db


# ___модели___
class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    template = db.Column(db.Text, nullable=False)

    variables = db.relationship(
        "TemplateVariable",
        backref="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Category {self.name}>"


class TemplateVariable(db.Model):
    __tablename__ = "template_variable"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id"),
        nullable=False,
    )
    name = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(150), nullable=False)
    field_type = db.Column(db.String(30), nullable=False)
    required = db.Column(db.Boolean, default=False, nullable=False)
    order = db.Column(db.Integer, nullable=True, default=1)

    options = db.relationship(
        "VariableOption",
        backref="variable",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "category_id",
            "name",
            name="unique_category_variable",
        ),
    )


class VariableOption(db.Model):
    __tablename__ = "variable_option"

    id = db.Column(db.Integer, primary_key=True)
    variable_id = db.Column(
        db.Integer,
        db.ForeignKey("template_variable.id"),
        nullable=False,
    )
    value = db.Column(db.String(255), nullable=False)
    output_value = db.Column(db.String(255), nullable=False)


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    diaries = db.relationship(
        "Diary",
        backref="user",
        cascade="all, delete-orphan",
    )


class Diary(db.Model):
    __tablename__ = "diary"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )

    number = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    entries = db.relationship(
        "DiaryEntry",
        backref="diary",
        cascade="all, delete-orphan",
        order_by="DiaryEntry.category_id",
    )

    laboratory_source = db.relationship(
        "LaboratorySource",
        back_populates="diary",
        uselist=False,
        cascade="all, delete-orphan",
    )
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "number",
            name="unique_user_diary_number",
        ),
    )


class DiaryEntry(db.Model):
    __tablename__ = "diary_entry"

    id = db.Column(db.Integer, primary_key=True)

    diary_id = db.Column(
        db.Integer,
        db.ForeignKey("diary.id"),
        nullable=False,
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id"),
        nullable=False,
    )

    text = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    syndromes = db.Column(db.Text, nullable=False, default="")
    form_data = db.Column(db.Text, nullable=False, default="{}")

    category = db.relationship("Category")

    __table_args__ = (
        db.UniqueConstraint(
            "diary_id",
            "category_id",
            name="unique_diary_category",
        ),
    )


class TherapyPurpose(db.Model):
    __tablename__ = "therapy_purpose"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    output_value = db.Column(db.String(200), nullable=False)


class TherapyGroup(db.Model):
    """Группа препаратов с общей целью терапии."""

    __tablename__ = "therapy_group"

    id = db.Column(db.Integer, primary_key=True)

    diary_id = db.Column(
        db.Integer,
        db.ForeignKey("diary.id"),
        nullable=False,
    )

    purpose_id = db.Column(
        db.Integer,
        db.ForeignKey("therapy_purpose.id"),
        nullable=False,
    )

    position = db.Column(db.Integer, nullable=False)

    purpose = db.relationship("TherapyPurpose")

    diary = db.relationship(
        "Diary",
        backref=db.backref(
            "therapy_groups",
            cascade="all, delete-orphan",
            order_by="TherapyGroup.position",
        ),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "diary_id",
            "purpose_id",
            name="unique_diary_therapy_purpose",
        ),
    )


class TherapyMedication(db.Model):
    """Справочник препаратов."""

    __tablename__ = "therapy_medication"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
