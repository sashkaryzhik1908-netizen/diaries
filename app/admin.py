from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from app.extensions import db

from .models import (
    Category,
    Diary,
    TemplateVariable,
    TherapyMedication,
    TherapyPurpose,
    User,
    VariableOption,
)


class SuperuserAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    @expose("/")
    def index(self):
        stats = {
            "users": User.query.count(),
            "categories": Category.query.count(),
            "variables": TemplateVariable.query.count(),
            "options": VariableOption.query.count(),
        }

        return self.render("admin/index.html", stats=stats)


class SuperuserModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        return self.render("403.html"), 403


class UserAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "username": "Имя пользователя",
        "is_superuser": "Суперпользователь",
        "is_admin": "Администратор",
    }
    column_formatters = {
        "is_superuser": lambda view, context, model, name: (
            "Да" if getattr(model, name) else "Нет"
        ),
        "is_admin": lambda view, context, model, name: (
            "Да" if getattr(model, name) else "Нет"
        ),
    }
    column_list = ("id", "username", "is_superuser", "is_admin")
    column_searchable_list = ("username",)
    column_default_sort = ("username", True)
    column_filters = ("is_superuser", "is_admin")
    column_sortable_list = ("id", "username", "is_superuser", "is_admin")
    form_columns = ("is_admin", "is_superuser")
    can_create = False
    can_delete = True


class CategoryAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "name": "Название",
        "slug": "Техническое название",
        "order": "Порядок",
        "template": "Шаблон",
    }
    column_list = (
        "id",
        "name",
        "slug",
        "order",
        "template",
    )
    column_searchable_list = ("name",)
    column_default_sort = ("id", False)
    form_columns = (
        "name",
        "slug",
        "order",
        "template",
    )


class TemplateVariableAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "name": "Техническое имя",
        "label": "Имя",
        "field_type": "Тип поля",
        "required": "Обязательно",
        "order": "Порядок",
        "category.name": "Категория",
    }
    column_formatters = {
        "required": lambda view, context, model, name: (
            "Да" if getattr(model, name) else "Нет"
        ),
    }
    column_list = ("label", "name", "field_type", "required", "category.name")
    column_searchable_list = ("name",)
    column_default_sort = ("name", False)
    column_filters = ("category.name",)
    form_columns = (
        "name",
        "label",
        "field_type",
        "required",
        "order",
        "category",
    )


class VariableOptionAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "value": "Значение",
        "output_value": "Отображаемое значение",
        "variable.label": "Шаблонная переменная",
    }
    column_list = ("id", "value", "output_value", "variable.label")
    column_searchable_list = ("value", "output_value", "variable.label")
    column_default_sort = ("id", False)
    column_filters = ("id", "value", "output_value")
    column_sortable_list = ("variable.label",)
    form_columns = (
        "value",
        "output_value",
        "variable",
    )


class DiaryAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "created_at": "Создан",
        "user.username": "Пользователь",
    }
    column_list = ("id", "created_at", "user.username")
    column_default_sort = ("id", False)
    form_columns = ("created_at",)
    can_create = False
    can_delete = True


class TherapyPurposeAdmin(SuperuserModelView):
    pass


class TherapyMedicationAdmin(SuperuserModelView):
    pass


def init_admin(app):
    admin = Admin(
        index_view=SuperuserAdminIndexView(),
    )

    admin.add_view(UserAdmin(User, db.session, name="Пользователи"))
    admin.add_view(CategoryAdmin(Category, db.session, name="Категории"))
    admin.add_view(
        TemplateVariableAdmin(TemplateVariable, db.session, name="Переменные")
    )
    admin.add_view(VariableOptionAdmin(VariableOption, db.session, name="Опции"))
    admin.add_view(DiaryAdmin(Diary, db.session, name="Дневники"))
    admin.add_view(TherapyPurposeAdmin(TherapyPurpose, db.session, name="Цели терапии"))
    admin.add_view(
        TherapyMedicationAdmin(TherapyMedication, db.session, name="Препараты")
    )

    admin.init_app(app)
