from flask import Blueprint, render_template, redirect, url_for, flash

from app.extensions import db
from app.models import Diary, Category


diaries_bp = Blueprint("diaries", __name__)


# Список дневников
@diaries_bp.route("/diaries")
def list_diaries():
    diaries = Diary.query.order_by(Diary.created_at.desc()).all()

    return render_template(
        "diares/diaries.html",
        diaries=diaries,
    )


# Создание дневника
@diaries_bp.route("/diaries/create", methods=["POST"])
def create_diary():
    diary = Diary()

    db.session.add(diary)
    db.session.commit()

    flash("Новый дневник создан.", "success")
    return redirect(url_for("diaries.view_diary", diary_id=diary.id))


# Просмотр дневника
@diaries_bp.route("/diaries/<int:diary_id>")
def view_diary(diary_id):
    diary = Diary.query.get_or_404(diary_id)

    diary.entries.sort(key=lambda entry: entry.category.order)

    categories = Category.query.order_by(Category.order).all()

    condition_entry = next(
        (entry for entry in diary.entries if entry.category.slug == "condition"),
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
    )


# Удаление дневника
@diaries_bp.route("/diaries/<int:diary_id>/delete", methods=["POST"])
def delete_diary(diary_id):
    diary = Diary.query.get_or_404(diary_id)

    db.session.delete(diary)
    db.session.commit()

    flash("Дневник удалён.", "success")
    return redirect(url_for("diaries.list_diaries"))
