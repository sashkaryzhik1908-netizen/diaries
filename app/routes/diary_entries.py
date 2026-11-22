import json

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app.extensions import db
from app.models import (
    Category,
    Diary,
    DiaryEntry,
    TemplateVariable,
    TherapyMedication,
    TherapyPurpose,
)
from app.services.diary_service import (
    process_category_form,
    process_prescriptions,
)

diary_entries_bp = Blueprint("diary_entries", __name__)


# Заполнение категории в дневнике
@diary_entries_bp.route(
    "/diaries/<int:diary_id>/categories/<int:category_id>/fill",
    methods=["GET", "POST"],
)
@login_required
def fill_category(diary_id, category_id):
    diary = db.first_or_404(
        select(Diary).where(
            Diary.id == diary_id,
            Diary.user_id == current_user.id,
        )
    )

    category = db.get_or_404(Category, category_id)

    entry = db.session.scalar(
        select(DiaryEntry).where(
            DiaryEntry.diary_id == diary.id,
            DiaryEntry.category_id == category.id,
        )
    )
    # Загружаем ранее сохранённые данные формы
    try:
        form_data = json.loads(entry.form_data) if entry and entry.form_data else {}
    except (json.JSONDecodeError, TypeError):
        current_app.logger.exception("Ошибка чтения данных формы дневника.")
        form_data = {}

    values = {}
    errors = []
    generated_text = None

    variables = db.session.scalars(
        select(TemplateVariable)
        .where(TemplateVariable.category_id == category.id)
        .order_by(TemplateVariable.order)
    ).all()

    if category.slug == "prescriptions":
        purposes = db.session.scalars(
            select(TherapyPurpose).order_by(TherapyPurpose.name)
        ).all()

        medications = db.session.scalars(
            select(TherapyMedication).order_by(TherapyMedication.name)
        ).all()

    else:
        purposes = []
        medications = []

    if request.method == "POST":
        # Сохраняем все отправленные поля формы
        form_data = request.form.to_dict(flat=False)

        if category.slug == "prescriptions":
            generated_text, errors = process_prescriptions(request.form)

        else:
            values, errors = process_category_form(
                request.form,
                variables,
                category,
            )

        if not errors:
            if generated_text is None:
                generated_text = current_app.jinja_env.from_string(
                    category.template
                ).render(**values)

            syndromes = ", ".join(values.get("syndromes", []))

            if entry:
                entry.text = generated_text
                entry.syndromes = syndromes if category.slug == "condition" else ""
                entry.form_data = json.dumps(
                    form_data,
                    ensure_ascii=False,
                )

            else:
                last_position = (
                    db.session.scalar(
                        select(func.max(DiaryEntry.position)).where(
                            DiaryEntry.diary_id == diary.id
                        )
                    )
                    or -1
                )

                entry = DiaryEntry(
                    diary_id=diary.id,
                    category_id=category.id,
                    text=generated_text,
                    position=last_position + 1,
                    syndromes=(syndromes if category.slug == "condition" else ""),
                    form_data=json.dumps(
                        form_data,
                        ensure_ascii=False,
                    ),
                )

                db.session.add(entry)

            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Ошибка при сохранении раздела дневника.")
                flash(
                    "Произошла ошибка при сохранении раздела дневника.",
                    "danger",
                )
                return render_template(
                    "diares/fill_category.html",
                    category=category,
                    diary=diary,
                    values=values,
                    variables=variables,
                    errors=errors,
                    generated_text=generated_text,
                    purposes=purposes,
                    medications=medications,
                    form_data=form_data,
                )

            flash(
                "Раздел дневника успешно сохранён.",
                "success",
            )

            return redirect(url_for("diaries.view_diary", diary_id=diary.id))

        else:
            flash(
                "Не удалось сохранить раздел. Проверьте обязательные поля.",
                "warning",
            )

    return render_template(
        "diares/fill_category.html",
        category=category,
        diary=diary,
        values=values,
        variables=variables,
        errors=errors,
        generated_text=generated_text,
        purposes=purposes,
        medications=medications,
        form_data=form_data,
    )
