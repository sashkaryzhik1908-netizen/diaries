from datetime import datetime

from sqlalchemy import select

from app.extensions import db
from app.models import TherapyMedication, TherapyPurpose, TherapySource


# Проверка анальгетической терапии
def is_analgesic_therapy(purpose):
    return purpose.name.lower() == "анальгетическая"


# Проверка антибактериальной терапии
def is_antibacterial_therapy(purpose):
    return purpose.name.lower() == "антибактериальная"


# Обработка назначений
def process_prescriptions(form):
    errors = []

    # Режим и диета
    regime = form.get("regime", "")
    diet = form.get("diet", "")

    hydrotation = form.get("hydrotation", "")
    volume = form.get("volume", "")

    sources = db.session.scalars(select(TherapySource)).all()

    sources_dict = {
        source.name: {value.name for value in source.values} for source in sources
    }

    allowed_units = sources_dict["Единицы измерения"]
    allowed_methods = sources_dict["Способы введения"]
    allowed_frequencies = sources_dict["Кратность"]

    # Получение индексов групп назначений
    group_indexes = sorted(
        {
            key[len("purpose_id[") : -1]
            for key in form
            if key.startswith("purpose_id[")
            and key.endswith("]")
            and key[len("purpose_id[") : -1].isdigit()
        },
        key=int,
    )

    if not group_indexes:
        errors.append("Добавьте хотя бы одно назначение.")

    # Получение ID целей терапии
    purpose_ids_int = [
        int(form.get(f"purpose_id[{index}]"))
        for index in group_indexes
        if form.get(f"purpose_id[{index}]", "").isdigit()
    ]

    # Получение ID препаратов
    medication_ids_int = []

    for index in group_indexes:
        medication_ids = form.getlist(f"medication_id[{index}][]")

        medication_ids_int.extend(
            int(value) for value in medication_ids if value.isdigit()
        )

    # Получение целей терапии из базы данных
    purposes_dict = {
        purpose.id: purpose
        for purpose in db.session.scalars(
            select(TherapyPurpose).where(TherapyPurpose.id.in_(purpose_ids_int))
        ).all()
    }

    # Получение препаратов из базы данных
    medications_dict = {
        medication.id: medication
        for medication in db.session.scalars(
            select(TherapyMedication).where(
                TherapyMedication.id.in_(medication_ids_int)
            )
        ).all()
    }

    groups = []

    # Обработка каждой группы назначений
    for index in group_indexes:
        # Получение цели терапии
        purpose_id = form.get(f"purpose_id[{index}]", "")

        if not purpose_id.isdigit() or int(purpose_id) not in purposes_dict:
            errors.append("Выберите корректную цель терапии.")
            continue

        purpose = purposes_dict[int(purpose_id)]

        # Получение препаратов, дозировок и единиц измерения
        medication_ids = form.getlist(f"medication_id[{index}][]")
        doses = form.getlist(f"dose[{index}][]")
        units = form.getlist(f"unit[{index}][]")

        if not medication_ids:
            errors.append("Добавьте хотя бы один препарат.")
            continue

        # Анальгетическая терапия
        if is_analgesic_therapy(purpose):
            medication_parts = []
            group_valid = True

            for medication_id in medication_ids:
                if (
                    not medication_id.isdigit()
                    or int(medication_id) not in medications_dict
                ):
                    errors.append("Выберите корректный препарат.")
                    group_valid = False
                    continue

                medication = medications_dict[int(medication_id)]
                medication_parts.append(medication.name)

            if not group_valid:
                continue

            # Формирование текста анальгетической терапии
            group_text = f"({', '.join(medication_parts)})"

            groups.append(
                {
                    "name": purpose.output_value,
                    "text": group_text,
                    "type": "analgesic",
                }
            )

            continue

        # Антибактериальная терапия
        if is_antibacterial_therapy(purpose):
            methods = form.getlist(f"medication_method[{index}][]")
            frequencies = form.getlist(f"medication_frequency[{index}][]")
            start_dates = form.getlist(f"medication_start_date[{index}][]")

            if not (
                len(medication_ids)
                == len(doses)
                == len(units)
                == len(methods)
                == len(frequencies)
                == len(start_dates)
            ):
                errors.append("Количество препаратов и их параметров не совпадает.")
                continue

            medication_parts = []
            group_valid = True

            # Проверка каждого препарата антибактериальной терапии
            for (
                medication_id,
                dose,
                unit,
                method,
                frequency,
                start_date,
            ) in zip(
                medication_ids,
                doses,
                units,
                methods,
                frequencies,
                start_dates,
            ):
                dose = dose.strip()
                frequency = frequency.strip()
                start_date = start_date.strip()

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

                if method not in allowed_methods:
                    errors.append(
                        "Выберите корректный способ введения каждого препарата."
                    )
                    group_valid = False
                    continue

                if frequency and frequency not in allowed_frequencies:
                    errors.append("Выберите корректную кратность.")
                    group_valid = False
                    continue

                formatted_date = ""

                if start_date:
                    try:
                        formatted_date = datetime.strptime(
                            start_date,
                            "%Y-%m-%d",
                        ).strftime("%d.%m.%Y")
                    except ValueError:
                        errors.append(
                            "Укажите корректную дату начала каждого препарата."
                        )
                        group_valid = False
                        continue

                medication = medications_dict[int(medication_id)]

                # Формирование текста отдельного препарата
                medication_text = f"{medication.name} {dose} {unit} {method}"

                if frequency:
                    medication_text += f" {frequency}"

                if formatted_date:
                    medication_text += f" (с {formatted_date})"

                medication_parts.append(medication_text)

            if not group_valid:
                continue

            # Объединение препаратов через запятую
            group_text = ", ".join(medication_parts)

            groups.append(
                {
                    "name": purpose.output_value,
                    "text": group_text,
                    "type": "antibacterial",
                }
            )

            continue

        # Проверка количества препаратов, дозировок и единиц измерения
        if len(medication_ids) != len(doses) or len(medication_ids) != len(units):
            errors.append(
                "Количество препаратов, дозировок и единиц измерения не совпадает."
            )
            continue

        medication_parts = []
        group_valid = True

        # Проверка препаратов и формирование их текста
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

        # Получение способа введения
        method = form.get(
            f"administration_method[{index}]",
            "",
        )

        if method not in allowed_methods:
            errors.append("Выберите корректный способ введения.")
            continue

        # Получение кратности
        frequency = form.get(
            f"frequency[{index}]",
            "",
        ).strip()

        if frequency and frequency not in allowed_frequencies:
            errors.append("Выберите корректную кратность.")
            continue

        # Получение даты начала
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

        # Объединение препаратов знаком +
        medications_text = " + ".join(medication_parts)

        # Формирование общего текста группы назначений
        group_text = " ".join(
            part for part in (medications_text, method, frequency) if part
        )

        if formatted_date:
            group_text += f" (с {formatted_date})"

        groups.append(
            {
                "name": purpose.output_value,
                "text": group_text,
                "type": "general",
            }
        )

    generated_text = None

    # Формирование итогового текста назначений
    if not errors:
        lines = [
            "В плане интенсивной терапии:",
            f"1. {regime}, диета {diet};",
            (
                f"2. Инфузионная терапия кристаллоидами, с учетом физ потребности, "
                f"текущих и патологических потерь, в режиме {hydrotation}, "
                f"в общем объеме до {volume} мл/сут;"
            ),
        ]

        # Добавление групп назначений в итоговый текст
        for number, group in enumerate(groups, start=3):
            if "тромботических" in group["name"]:
                lines.append(f"{number}. {group['name']} {group['text']};")

            elif group["type"] == "analgesic":
                lines.append(f"{number}. {group['name']} {group['text']};")

            else:
                lines.append(f"{number}. {group['name']}: {group['text']};")

        # Добавление общих мероприятий интенсивной терапии
        lines.extend(
            [
                (
                    f"{len(groups) + 3}. Мониторинг витальных функций: "
                    "АД, ЧСС/пульс, сатурация О2, почасовой диурез, "
                    "Т-тела, ЭКГ-мониторинг во II отведении 3-ми электродами;"
                ),
                (
                    f"{len(groups) + 4}. Мероприятия общего ухода, "
                    f"суточный мониторинг, контроль лабораторных данных."
                ),
            ]
        )

        generated_text = "\n".join(lines).strip()

    return generated_text, errors
