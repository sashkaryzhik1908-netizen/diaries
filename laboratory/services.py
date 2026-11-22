import re
from collections import defaultdict
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from sqlalchemy import select

from app.extensions import db
from laboratory.models import (
    LaboratoryAlias,
    LaboratoryCategory,
    LaboratoryIndicator,
    LaboratorySource,
)
from laboratory.parser import parse_laboratory_text


def format_indicator_value(value, precision):
    """Округляет значение показателя с заданной точностью."""

    if precision is None:
        return value

    match = re.match(
        r"^(?P<prefix>\s*[<>≤≥]?\s*)(?P<number>-?\d+(?:[.,]\d+)?)(?P<suffix>.*)$",
        value,
    )

    if not match:
        return value

    try:
        number = Decimal(match.group("number").replace(",", "."))
        rounding = Decimal(1).scaleb(-precision)

        rounded = number.quantize(
            rounding,
            rounding=ROUND_HALF_UP,
        )

    except InvalidOperation:
        return value

    decimal_separator = "," if "," in match.group("number") else "."

    formatted = f"{rounded:.{precision}f}"

    if decimal_separator == ",":
        formatted = formatted.replace(".", ",")

    return match.group("prefix") + formatted + match.group("suffix")


def format_laboratory_results(results):
    """Формирует текст лабораторных исследований в динамике."""

    indicators_from_db = {
        indicator.id: indicator
        for indicator in db.session.scalars(select(LaboratoryIndicator)).all()
    }

    indicator_order = {
        "cbc": [
            "HGB",
            "RBC",
            "WBC",
            "HCT",
            "PLT",
            "ESR",
        ],
        "manual_diff": [
            "BAND",
            "SEG",
            "LYM",
            "MON",
            "META",
            "MYELO",
        ],
        "coagulogram": [
            "APTT",
            "FIB",
            "INR",
            "PT",
            "PTI",
            "DDIMER",
        ],
        "biochemistry": [
            "TP",
            "ALB",
            "ALT",
            "AST",
            "DBIL",
            "TBIL",
            "K",
            "NA",
            "GLU",
            "UREA",
            "CREA",
            "CRP",
            "PCT",
            "AMY",
            "HbA1c",
            "CL",
            "CA",
            "MG",
            "LDH",
            "ALP",
            "GGT",
            "TNI",
            "CKMB",
        ],
    }

    # Сортируем результаты по дате и времени.
    sorted_results = sorted(
        results,
        key=lambda item: datetime.strptime(
            item["datetime"],
            "%d.%m.%Y %H:%M",
        ),
    )

    grouped_results = defaultdict(dict)

    for result in sorted_results:
        category = result["category"]
        code = result["code"]

        # Ручную лейкоформулу выделяем отдельно.
        if category == "cbc" and code in indicator_order["manual_diff"]:
            section = "manual_diff"
        else:
            section = category

        indicator_id = result["indicator_id"]
        db_indicator = indicators_from_db.get(indicator_id)

        if indicator_id not in grouped_results[section]:
            grouped_results[section][indicator_id] = {
                "name": result["indicator"],
                "code": code,
                "values": [],
                "unit": db_indicator.unit if db_indicator else None,
            }

        indicator = grouped_results[section][indicator_id]

        # Индивидуальное округление показателя.
        precision = db_indicator.precision if db_indicator else None

        value = format_indicator_value(
            result["value"],
            precision,
        )

        indicator["values"].append(value)

    section_order = [
        ("cbc", "ОАК"),
        ("manual_diff", "Подсчет лейкоформулы"),
        ("coagulogram", "Коагулограмма"),
        ("biochemistry", "Б/х крови"),
        ("bacteriology", "Бактериологические исследования"),
    ]

    lines = []

    for section, section_name in section_order:
        indicators = grouped_results.get(section)

        if not indicators:
            continue

        lines.append(f"{section_name}:")

        order = indicator_order.get(section, [])

        ordered_indicators = sorted(
            indicators.values(),
            key=lambda item: (
                order.index(item["code"]) if item["code"] in order else 999
            ),
        )

        for indicator in ordered_indicators:
            name = indicator["name"]
            values = "-".join(indicator["values"])

            result_text = f"{name} — {values}"

            if indicator["unit"]:
                result_text += f" {indicator['unit']}"

            lines.append(result_text + ";")

        lines.append("")

    return "\n".join(lines).strip()


def generate_laboratory_text(source_text):
    """Разбирает исходный текст и формирует итоговый текст."""

    results = parse_laboratory_text(source_text)

    return format_laboratory_results(results)


def get_laboratory_categories():
    """Получает список категорий лабораторных исследований."""
    return db.session.scalars(
        select(LaboratoryCategory).order_by(LaboratoryCategory.name)
    ).all()


def get_category_indicators(category_id):
    """Получает показатели лабораторной категории."""
    return db.session.scalars(
        select(LaboratoryIndicator)
        .where(LaboratoryIndicator.category_id == category_id)
        .order_by(LaboratoryIndicator.name)
    ).all()


def create_laboratory_category(name, slug):
    """Создаёт категорию лабораторных исследований."""
    category = LaboratoryCategory(
        name=name,
        slug=slug,
    )

    db.session.add(category)
    db.session.commit()

    return category


def update_laboratory_category(category, name, slug):
    """Изменяет категорию лабораторных исследований."""
    category.name = name
    category.slug = slug

    db.session.commit()


def delete_laboratory_category(category):
    """Удаляет категорию лабораторных исследований."""
    db.session.delete(category)
    db.session.commit()


def create_laboratory_indicator(
    category_id,
    name,
    code,
    unit,
    precision,
):
    """Создаёт лабораторный показатель."""
    indicator = LaboratoryIndicator(
        category_id=category_id,
        name=name,
        code=code,
        unit=unit,
        precision=precision,
    )

    db.session.add(indicator)
    db.session.commit()

    return indicator


def update_laboratory_indicator(
    indicator,
    category_id,
    name,
    code,
    unit,
    precision,
):
    """Изменяет лабораторный показатель."""
    indicator.category_id = category_id
    indicator.name = name
    indicator.code = code
    indicator.unit = unit
    indicator.precision = precision

    db.session.commit()


def delete_laboratory_indicator(indicator):
    """Удаляет лабораторный показатель."""
    db.session.delete(indicator)
    db.session.commit()


def get_indicator_aliases(indicator_id):
    """Получает альтернативные названия лабораторного показателя."""
    return db.session.scalars(
        select(LaboratoryAlias)
        .where(LaboratoryAlias.indicator_id == indicator_id)
        .order_by(LaboratoryAlias.alias)
    ).all()


def create_laboratory_alias(indicator_id, alias_text):
    """Создаёт альтернативное название лабораторного показателя."""
    alias = LaboratoryAlias(
        indicator_id=indicator_id,
        alias=alias_text,
    )

    db.session.add(alias)
    db.session.commit()

    return alias


def update_laboratory_alias(alias, indicator_id, alias_text):
    """Изменяет альтернативное название лабораторного показателя."""
    alias.indicator_id = indicator_id
    alias.alias = alias_text

    db.session.commit()


def delete_laboratory_alias(alias):
    """Удаляет альтернативное название лабораторного показателя."""
    db.session.delete(alias)
    db.session.commit()


def save_laboratory_source(diary_id, source, source_text, result_text):
    """Сохраняет исходный и обработанный лабораторный текст."""
    if source is None:
        source = LaboratorySource(
            diary_id=diary_id,
            source_text=source_text,
            result_text=result_text,
        )

        db.session.add(source)

    else:
        source.source_text = source_text
        source.result_text = result_text

    db.session.commit()

    return source
