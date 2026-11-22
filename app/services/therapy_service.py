from sqlalchemy import select

from app.extensions import db
from app.models import TherapyGroup, TherapyMedication, TherapyPurpose

# ___Цели терапии___


# Получение списка целей терапии
def get_therapy_purposes():
    return db.session.scalars(
        select(TherapyPurpose).order_by(TherapyPurpose.name)
    ).all()


# Проверка существования цели терапии
def get_existing_purpose(name, exclude_id=None):
    query = select(TherapyPurpose).where(TherapyPurpose.name == name)

    if exclude_id is not None:
        query = query.where(TherapyPurpose.id != exclude_id)

    return db.session.scalar(query)


# Добавление цели терапии
def create_therapy_purpose(name, output_value):
    purpose = TherapyPurpose(
        name=name,
        output_value=output_value,
    )

    db.session.add(purpose)
    db.session.commit()

    return purpose


# Редактирование цели терапии
def update_therapy_purpose(purpose, name, output_value):
    purpose.name = name
    purpose.output_value = output_value

    db.session.commit()

    return purpose


# Проверка использования цели терапии
def is_purpose_used(purpose_id):
    return (
        db.session.scalar(
            select(TherapyGroup).where(TherapyGroup.purpose_id == purpose_id)
        )
        is not None
    )


# Удаление цели терапии
def delete_therapy_purpose(purpose):
    db.session.delete(purpose)
    db.session.commit()


# ___Препараты___


# Получение списка препаратов
def get_therapy_medications():
    return db.session.scalars(
        select(TherapyMedication).order_by(TherapyMedication.name)
    ).all()


# Проверка существования препарата
def get_existing_medication(name, exclude_id=None):
    query = select(TherapyMedication).where(TherapyMedication.name == name)

    if exclude_id is not None:
        query = query.where(TherapyMedication.id != exclude_id)

    return db.session.scalar(query)


# Добавление препарата
def create_therapy_medication(name):
    medication = TherapyMedication(name=name)

    db.session.add(medication)
    db.session.commit()

    return medication


# Редактирование препарата
def update_therapy_medication(medication, name):
    medication.name = name

    db.session.commit()

    return medication


# Удаление препарата
def delete_therapy_medication(medication):
    db.session.delete(medication)
    db.session.commit()
