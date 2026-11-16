import json

from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    url_for,
    request,
    flash,
)

from app.extensions import db


from app.services.diary_service import (
    process_prescriptions,
    process_category_form,
)

from app.models import (
    Category,
    TemplateVariable,
    Diary,
    DiaryEntry,
    TherapyPurpose,
    TherapyMedication,
)

diary_entries_bp = Blueprint("diary_entries", __name__)


# Заполнение категории в дневнике
@diary_entries_bp.route(
    "/diaries/<int:diary_id>/categories/<int:category_id>/fill",
    methods=["GET", "POST"],
)
def fill_category(diary_id, category_id):
    diary = Diary.query.get_or_404(diary_id)
    category = Category.query.get_or_404(category_id)

    entry = DiaryEntry.query.filter_by(
        diary_id=diary.id,
        category_id=category.id,
    ).first()

    # Загружаем ранее сохранённые данные формы
    form_data = json.loads(entry.form_data) if entry and entry.form_data else {}

    values = {}
    errors = []
    generated_text = None

    variables = (
        TemplateVariable.query.filter_by(category_id=category.id)
        .order_by(TemplateVariable.id)
        .all()
    )

    if category.slug == "prescriptions":
        purposes = TherapyPurpose.query.order_by(
            TherapyPurpose.order,
            TherapyPurpose.id,
        ).all()

        medications = TherapyMedication.query.order_by(
            TherapyMedication.name,
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

                if category.slug == "condition":
                    entry.syndromes = syndromes

                entry.form_data = json.dumps(
                    form_data,
                    ensure_ascii=False,
                )

            else:
                last_position = max(
                    (item.position for item in diary.entries),
                    default=-1,
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

            db.session.commit()

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
