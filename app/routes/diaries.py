from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app.extensions import db
from app.models import Category, Diary, DiaryEntry

diaries_bp = Blueprint("diaries", __name__)


# Список дневников
@diaries_bp.route("/diaries")
@login_required
def list_diaries():
    diaries = db.session.scalars(
        select(Diary)
        .where(Diary.user_id == current_user.id)
        .order_by(Diary.created_at.desc())
    ).all()

    return render_template(
        "diares/diaries.html",
        diaries=diaries,
    )


# Создание дневника
@diaries_bp.route("/diaries/create", methods=["POST"])
@login_required
def create_diary():
    last_number = (
        db.session.scalar(
            select(func.max(Diary.number)).where(Diary.user_id == current_user.id)
        )
        or 0
    )

    diary = Diary(
        user_id=current_user.id,
        number=last_number + 1,
    )

    db.session.add(diary)

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Ошибка при создании дневника.")
        flash("Не удалось создать дневник.", "danger")
        return redirect(url_for("diaries.list_diaries"))

    flash("Новый дневник создан.", "success")

    return redirect(url_for("diaries.view_diary", diary_id=diary.id))


# Просмотр дневника
@diaries_bp.route("/diaries/<int:diary_id>")
@login_required
def view_diary(diary_id):
    diary = db.first_or_404(
        select(Diary).where(
            Diary.id == diary_id,
            Diary.user_id == current_user.id,
        )
    )

    entries = db.session.scalars(
        select(DiaryEntry)
        .where(DiaryEntry.diary_id == diary.id)
        .join(Category, DiaryEntry.category_id == Category.id)
        .order_by(Category.order)
    ).all()

    categories = db.session.scalars(select(Category).order_by(Category.order)).all()

    condition_entry = next(
        (entry for entry in entries if entry.category.slug == "condition"),
        None,
    )

    syndromes = (
        condition_entry.syndromes.split(", ")
        if condition_entry and condition_entry.syndromes
        else []
    )

    return render_template(
        "diares/view_diary.html",
        diary=diary,
        categories=categories,
        syndromes=syndromes,
        entries=entries,
    )


# Удаление дневника
@diaries_bp.route("/diaries/<int:diary_id>/delete", methods=["POST"])
@login_required
def delete_diary(diary_id):
    diary = db.first_or_404(
        select(Diary).where(
            Diary.id == diary_id,
            Diary.user_id == current_user.id,
        )
    )

    db.session.delete(diary)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Ошибка при удалении дневника.")
        flash("Не удалось удалить дневник.", "danger")
        return redirect(url_for("diaries.list_diaries"))

    flash("Дневник удалён.", "success")

    return redirect(url_for("diaries.list_diaries"))
