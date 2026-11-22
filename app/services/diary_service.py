from datetime import datetime
from datetime import timezone
from zoneinfo import ZoneInfo

from app.models import (
    TherapyPurpose,
    TherapyMedication,
    VariableOption,
)

LOCAL_TIMEZONE = ZoneInfo("Asia/Almaty")


def to_local_time(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(LOCAL_TIMEZONE)

# Обработка назначений
def process_prescriptions(form):
    errors = []

    # Режим и диета
    regime = form.get("regime", "")
    diet = form.get("diet", "")

    hydrotation = form.get("hydrotation", "")
    volume = form.get("volume", "")

    allowed_units = {
        "мл",
        "мг",
        "гр",
        "ед",
        "МЕ",
        "мкг",
        "л",
        "мкг/кг/мин",
    }

    allowed_methods = {
        "внутривенно",
        "внутривенно капельно",
        "внутривенно, путём микроструйной перфузионной подачи",
        "внутримышечно",
        "подкожно",
        "перорально",
        "через назогастральный зонд",
        "ингаляционно",
        "наружно",
        "внутривенно, путём микроструйной перфузионной подачи, под контролем показателей гемодинамики с целевым срАД не менее 65 мм рт.ст",
    }

    allowed_frequencies = {
        *(f"{number} р/д" for number in range(1, 11)),
        "непрерывно",
        "по показаниям",
    }

    # Получаем индексы групп назначений
    group_indexes = sorted(
        {
            key[len("purpose_id[") : -1]
            for key in form.keys()
            if key.startswith("purpose_id[")
            and key.endswith("]")
            and key[len("purpose_id[") : -1].isdigit()
        },
        key=int,
    )

    if not group_indexes:
        errors.append("Добавьте хотя бы одно назначение.")

    # Получаем все ID целей терапии
    purpose_ids_int = [
        int(form.get(f"purpose_id[{index}]"))
        for index in group_indexes
        if form.get(f"purpose_id[{index}]", "").isdigit()
    ]

    # Получаем все ID препаратов
    medication_ids_int = []

    for index in group_indexes:
        medication_ids = form.getlist(f"medication_id[{index}][]")

        medication_ids_int.extend(
            int(value) for value in medication_ids if value.isdigit()
        )

    purposes_dict = {
        purpose.id: purpose
        for purpose in TherapyPurpose.query.filter(
            TherapyPurpose.id.in_(purpose_ids_int)
        ).all()
    }

    medications_dict = {
        medication.id: medication
        for medication in TherapyMedication.query.filter(
            TherapyMedication.id.in_(medication_ids_int)
        ).all()
    }

    groups = []

    for index in group_indexes:
        # Цель терапии
        purpose_id = form.get(
            f"purpose_id[{index}]",
            "",
        )

        if not purpose_id.isdigit() or int(purpose_id) not in purposes_dict:
            errors.append("Выберите корректную цель терапии.")
            continue

        purpose = purposes_dict[int(purpose_id)]

        # Препараты, дозировки и единицы измерения
        medication_ids = form.getlist(f"medication_id[{index}][]")
        doses = form.getlist(f"dose[{index}][]")
        units = form.getlist(f"unit[{index}][]")

        if not medication_ids:
            errors.append("Добавьте хотя бы один препарат.")
            continue

        if len(medication_ids) != len(doses) or len(medication_ids) != len(units):
            errors.append(
                "Количество препаратов, дозировок и единиц измерения не совпадает."
            )
            continue

        medication_parts = []
        group_valid = True

        for medication_id, dose, unit in zip(
            medication_ids,
            doses,
            units,
        ):
            dose = dose.strip()

            if (
                not medication_id.isdigit()
                or int(medication_id) not in medications_dict
            ):
                errors.append("Выберите корректный препарат.")
                group_valid = False
                continue

            if not dose:
                errors.append("Укажите дозу каждого препарата.")
                group_valid = False
                continue

            if unit not in allowed_units:
                errors.append("Выберите корректную единицу измерения.")
                group_valid = False
                continue

            medication = medications_dict[int(medication_id)]

            medication_parts.append(f"{medication.name} {dose} {unit}")

        if not group_valid:
            continue

        # Общий способ введения
        method = form.get(
            f"administration_method[{index}]",
            "",
        )

        if method not in allowed_methods:
            errors.append("Выберите корректный способ введения.")
            continue

        # Общая кратность
        frequency = form.get(
            f"frequency[{index}]",
            "",
        ).strip()

        if frequency and frequency not in allowed_frequencies:
            errors.append("Выберите корректную кратность.")
            continue

        # Общая дата начала
        start_date = form.get(
            f"start_date[{index}]",
            "",
        ).strip()

        formatted_date = ""

        if start_date:
            try:
                formatted_date = datetime.strptime(
                    start_date,
                    "%Y-%m-%d",
                ).strftime("%d.%m.%Y")

            except ValueError:
                errors.append("Укажите корректную дату начала.")
                continue

        # Объединяем препараты знаком +
        medications_text = " + ".join(medication_parts)

        # Общие параметры добавляем один раз
        # Общие параметры добавляем один раз
        group_text = " ".join(
            part for part in (medications_text, method, frequency) if part
        )

        if formatted_date:
            group_text += f" (с {formatted_date})"

        groups.append(
            {
                "name": purpose.output_value,
                "text": group_text,
            }
        )

    generated_text = None

    # Формируем итоговый текст
    if not errors:
        lines = [
            "В плане интенсивной терапии:",
            f"1. Режим {regime}, диета {diet};",
            f"2. Инфузионная терапия кристаллоидами, с учетом физ потребности, текущих и патологических потерь, в режиме {hydrotation}, в общем объеме до {volume} мл/сут;",
        ]

        for number, group in enumerate(groups, start=3):
            if "тромботических" in group["name"]:
                lines.append(f"{number}. {group['name']} {group['text']};")
            else:
                lines.append(f"{number}. {group['name']}: {group['text']};")



        # Общие мероприятия интенсивной терапии
        lines.extend(
            [
                f"{len(groups) + 3}. Мониторинг витальных функций: "
                "АД, ЧСС/пульс, сатурация О2, почасовой диурез, "
                "Т-тела, ЭКГ-мониторинг во II отведении 3-мя электродами;",
                f"{len(groups) + 4}. Мероприятия общего ухода, "
                "суточный мониторинг, контроль лабораторных данных.",
            ]
        )

        generated_text = "\n".join(lines).strip()

    return generated_text, errors


# Обработка обычных категорий
def process_category_form(form, variables, category):
    values = {}
    errors = []

    for variable in variables:
        if variable.field_type == "multiselect":
            raw_selected_ids = form.get(variable.name, "").split(",")

            if any(
                option_id and not option_id.isdigit() for option_id in raw_selected_ids
            ):
                errors.append(
                    f"Выбраны некорректные варианты в поле «{variable.label}»."
                )
                values[variable.name] = ""
                continue

            selected_ids = [option_id for option_id in raw_selected_ids if option_id]

            if len(selected_ids) != len(set(selected_ids)):
                errors.append(
                    f"В поле «{variable.label}» обнаружены повторяющиеся варианты."
                )
                values[variable.name] = ""
                continue

            selected_options = VariableOption.query.filter(
                VariableOption.variable_id == variable.id,
                VariableOption.id.in_([int(option_id) for option_id in selected_ids]),
            ).all()

            options = {str(option.id): option for option in selected_options}

            if len(options) != len(selected_ids):
                errors.append(
                    f"В поле «{variable.label}» выбраны недопустимые варианты."
                )

            if variable.name == "drug":
                drug_parts = []

                for option_id in selected_ids:
                    option = options.get(option_id)

                    if not option:
                        continue

                    dose = form.get(
                        f"dose_{option_id}",
                        "",
                    ).strip()

                    if not dose:
                        errors.append(f"Укажите дозировку препарата «{option.value}».")
                        continue

                    drug_parts.append(f"{option.output_value} в дозе {dose} мкг/кг/мин")

                values[variable.name] = ", ".join(drug_parts)

            else:
                values[variable.name] = ", ".join(
                    options[option_id].output_value
                    for option_id in selected_ids
                    if option_id in options
                )

            if variable.name == "reasons":
                values["syndromes"] = [
                    options[option_id].value
                    for option_id in selected_ids
                    if option_id in options
                ]

        elif variable.field_type == "select":
            selected = form.get(
                variable.name,
                "",
            )

            option = next(
                (option for option in variable.options if option.value == selected),
                None,
            )

            if selected and not option:
                errors.append(f"Выбран недопустимый вариант в поле «{variable.label}».")

            values[variable.name] = option.output_value if option else ""

        elif variable.field_type == "date":
            date_value = form.get(
                variable.name,
                "",
            ).strip()

            if date_value:
                try:
                    values[variable.name] = datetime.strptime(
                        date_value,
                        "%Y-%m-%d",
                    ).strftime("%d.%m.%Y")

                except ValueError:
                    errors.append(f"Укажите корректную дату в поле «{variable.label}».")
                    values[variable.name] = ""
            else:
                values[variable.name] = ""

        else:
            values[variable.name] = form.get(
                variable.name,
                "",
            ).strip()

        if variable.required and not values[variable.name]:
            if variable.name != "dose":
                errors.append(f"Заполните поле «{variable.label}».")

    # Старое общее поле дозировки больше не используется
    if any(variable.name == "drug" for variable in variables):
        values["dose"] = ""

    if category.slug == "complaints":
        custom_complaints = form.get(
            "custom_complaints",
            "",
        ).strip()

        if custom_complaints:
            values["custom_complaints"] = f", {custom_complaints}"
        else:
            values["custom_complaints"] = ""

    return values, errors
