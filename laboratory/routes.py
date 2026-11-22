from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.decorators import admin_required
from app.extensions import db
from app.models import Diary
from laboratory import services as laboratory_service
from laboratory.forms import (
    LaboratoryAliasForm,
    LaboratoryCategoryForm,
    LaboratoryIndicatorForm,
    LaboratorySourceForm,
)
from laboratory.models import (
    LaboratoryAlias,
    LaboratoryCategory,
    LaboratoryIndicator,
)

laboratory_bp = Blueprint(
    "laboratory",
    __name__,
    template_folder="templates",
)


# ==========================================================
# КАТЕГОРИИ ЛАБОРАТОРНЫХ ИССЛЕДОВАНИЙ
# ==========================================================


@laboratory_bp.route("/laboratory/categories")
@login_required
@admin_required
def list_categories():
    """Список категорий лабораторных исследований."""
    categories = laboratory_service.get_laboratory_categories()

    return render_template(
        "laboratory/list_categories.html",
        categories=categories,
    )


@laboratory_bp.route("/laboratory/categories/<int:category_id>")
@login_required
@admin_required
def view_category(category_id):
    """Просмотр категории и её показателей."""
    category = db.get_or_404(LaboratoryCategory, category_id)

    indicators = laboratory_service.get_category_indicators(category.id)

    return render_template(
        "laboratory/view_category.html",
        category=category,
        indicators=indicators,
    )


@laboratory_bp.route("/laboratory/categories/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_category():
    """Добавление категории лабораторных исследований."""
    form = LaboratoryCategoryForm()

    if form.validate_on_submit():
        category = laboratory_service.create_laboratory_category(
            name=form.name.data,
            slug=form.slug.data,
        )

        flash("Категория добавлена.", "success")

        return redirect(
            url_for(
                "laboratory.view_category",
                category_id=category.id,
            )
        )

    return render_template(
        "laboratory/add_category.html",
        form=form,
    )


@laboratory_bp.route(
    "/laboratory/categories/edit/<int:category_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_category(category_id):
    """Редактирование категории лабораторных исследований."""
    category = db.get_or_404(LaboratoryCategory, category_id)
    form = LaboratoryCategoryForm(obj=category)

    if form.validate_on_submit():
        laboratory_service.update_laboratory_category(
            category=category,
            name=form.name.data,
            slug=form.slug.data,
        )

        flash("Категория изменена.", "success")

        return redirect(
            url_for(
                "laboratory.view_category",
                category_id=category.id,
            )
        )

    return render_template(
        "laboratory/add_category.html",
        form=form,
        category=category,
    )


@laboratory_bp.route(
    "/laboratory/categories/delete/<int:category_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_category(category_id):
    """Удаление категории лабораторных исследований."""
    category = db.get_or_404(LaboratoryCategory, category_id)

    laboratory_service.delete_laboratory_category(category)

    flash("Категория удалена.", "success")

    return redirect(url_for("laboratory.list_categories"))


# ==========================================================
# ЛАБОРАТОРНЫЕ ПОКАЗАТЕЛИ
# ==========================================================


@laboratory_bp.route(
    "/laboratory/indicators/add/<int:category_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_indicator(category_id):
    """Добавление лабораторного показателя."""
    category = db.get_or_404(LaboratoryCategory, category_id)
    form = LaboratoryIndicatorForm()

    categories = db.session.scalars(
        select(LaboratoryCategory).order_by(LaboratoryCategory.name)
    ).all()

    form.category_id.choices = [(item.id, item.name) for item in categories]

    if form.validate_on_submit():
        laboratory_service.create_laboratory_indicator(
            category_id=category.id,
            name=form.name.data,
            code=form.code.data or None,
            unit=form.unit.data or None,
            precision=form.precision.data,
        )

        flash("Показатель добавлен.", "success")

        return redirect(
            url_for(
                "laboratory.view_category",
                category_id=category.id,
            )
        )

    if not form.is_submitted():
        form.category_id.data = category.id

    return render_template(
        "laboratory/add_indicator.html",
        form=form,
        category=category,
    )


@laboratory_bp.route(
    "/laboratory/indicators/edit/<int:indicator_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_indicator(indicator_id):
    """Редактирование лабораторного показателя."""
    indicator = db.get_or_404(LaboratoryIndicator, indicator_id)
    form = LaboratoryIndicatorForm(obj=indicator)

    categories = db.session.scalars(
        select(LaboratoryCategory).order_by(LaboratoryCategory.name)
    ).all()

    form.category_id.choices = [(item.id, item.name) for item in categories]

    if form.validate_on_submit():
        category_id = form.category_id.data

        laboratory_service.update_laboratory_indicator(
            indicator=indicator,
            category_id=category_id,
            name=form.name.data,
            code=form.code.data or None,
            unit=form.unit.data or None,
            precision=form.precision.data,
        )

        flash("Показатель изменён.", "success")

        return redirect(
            url_for(
                "laboratory.view_category",
                category_id=category_id,
            )
        )

    return render_template(
        "laboratory/add_indicator.html",
        form=form,
        indicator=indicator,
    )


@laboratory_bp.route(
    "/laboratory/indicators/delete/<int:indicator_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_indicator(indicator_id):
    """Удаление лабораторного показателя."""
    indicator = db.get_or_404(LaboratoryIndicator, indicator_id)
    category_id = indicator.category_id

    laboratory_service.delete_laboratory_indicator(indicator)

    flash("Показатель удалён.", "success")

    return redirect(
        url_for(
            "laboratory.view_category",
            category_id=category_id,
        )
    )


# ==========================================================
# АЛЬТЕРНАТИВНЫЕ НАЗВАНИЯ ПОКАЗАТЕЛЕЙ
# ==========================================================


@laboratory_bp.route(
    "/laboratory/aliases/<int:indicator_id>",
)
@login_required
@admin_required
def list_aliases(indicator_id):
    """Список альтернативных названий показателя."""
    indicator = db.get_or_404(LaboratoryIndicator, indicator_id)

    aliases = laboratory_service.get_indicator_aliases(indicator.id)

    return render_template(
        "laboratory/list_aliases.html",
        indicator=indicator,
        aliases=aliases,
    )


@laboratory_bp.route(
    "/laboratory/aliases/add/<int:indicator_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_alias(indicator_id):
    """Добавление альтернативного названия показателя."""
    indicator = db.get_or_404(LaboratoryIndicator, indicator_id)
    form = LaboratoryAliasForm()

    indicators = db.session.scalars(
        select(LaboratoryIndicator).order_by(LaboratoryIndicator.name)
    ).all()

    form.indicator_id.choices = [(item.id, item.name) for item in indicators]

    if form.validate_on_submit():
        laboratory_service.create_laboratory_alias(
            indicator_id=indicator.id,
            alias_text=form.alias.data,
        )

        flash("Альтернативное название добавлено.", "success")

        return redirect(
            url_for(
                "laboratory.list_aliases",
                indicator_id=indicator.id,
            )
        )

    if not form.is_submitted():
        form.indicator_id.data = indicator.id

    return render_template(
        "laboratory/add_alias.html",
        form=form,
        indicator=indicator,
    )


@laboratory_bp.route(
    "/laboratory/aliases/edit/<int:alias_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_alias(alias_id):
    """Редактирование альтернативного названия показателя."""
    alias = db.get_or_404(LaboratoryAlias, alias_id)
    form = LaboratoryAliasForm(obj=alias)

    indicators = db.session.scalars(
        select(LaboratoryIndicator).order_by(LaboratoryIndicator.name)
    ).all()

    form.indicator_id.choices = [(item.id, item.name) for item in indicators]

    if form.validate_on_submit():
        target_indicator = db.get_or_404(
            LaboratoryIndicator,
            form.indicator_id.data,
        )

        laboratory_service.update_laboratory_alias(
            alias=alias,
            indicator_id=target_indicator.id,
            alias_text=form.alias.data,
        )

        flash("Альтернативное название изменено.", "success")

        return redirect(
            url_for(
                "laboratory.list_aliases",
                indicator_id=target_indicator.id,
            )
        )

    return render_template(
        "laboratory/add_alias.html",
        form=form,
        alias=alias,
    )


@laboratory_bp.route(
    "/laboratory/aliases/delete/<int:alias_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_alias(alias_id):
    """Удаление альтернативного названия показателя."""
    alias = db.get_or_404(LaboratoryAlias, alias_id)
    indicator_id = alias.indicator_id

    laboratory_service.delete_laboratory_alias(alias)

    flash("Альтернативное название удалено.", "success")

    return redirect(
        url_for(
            "laboratory.list_aliases",
            indicator_id=indicator_id,
        )
    )


# ==========================================================
# ИСХОДНЫЙ ТЕКСТ ЛАБОРАТОРНЫХ ИССЛЕДОВАНИЙ
# ==========================================================


@laboratory_bp.route(
    "/laboratory/diary/<int:diary_id>",
    methods=["GET", "POST"],
)
@login_required
def diary_laboratory(diary_id):
    """Заполнение лабораторных исследований для дневника."""

    diary = db.first_or_404(
        select(Diary).where(
            Diary.id == diary_id,
            Diary.user_id == current_user.id,
        )
    )

    source = diary.laboratory_source

    form = LaboratorySourceForm()

    if form.validate_on_submit():
        source_text = form.source_text.data

        # Формирование обработанного лабораторного текста.
        result_text = laboratory_service.generate_laboratory_text(source_text)

        try:
            laboratory_service.save_laboratory_source(
                diary_id=diary.id,
                source=source,
                source_text=source_text,
                result_text=result_text,
            )

            flash("Лабораторный текст сохранён.", "success")

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Ошибка при сохранении лабораторного текста.")
            flash("Не удалось сохранить лабораторный текст.", "danger")

        return redirect(
            url_for(
                "diaries.view_diary",
                diary_id=diary.id,
            )
        )

    if source is not None:
        form.source_text.data = source.source_text

    return render_template(
        "laboratory/diary_source.html",
        form=form,
        diary=diary,
        source=source,
    )
