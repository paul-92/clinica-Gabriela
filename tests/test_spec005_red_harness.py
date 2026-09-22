from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.database.session import Base
from backend.models import (  # noqa: F401
    appointment,
    clinical_record,
    finance,
    patient,
    psychologist,
    settings,
    user,
)
from backend.schemas.finance import PaymentCreate


def _columns(table):
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return {item["name"]: item for item in inspect(engine).get_columns(table)}


def test_ac001_canonical_schema_uses_positive_integer_cents_only():
    payment_columns = _columns("payments")
    expense_columns = _columns("expenses")

    assert "amount" not in payment_columns
    assert "amount" not in expense_columns
    assert payment_columns["amount_cents"]["type"].python_type is int
    assert expense_columns["amount_cents"]["type"].python_type is int

    with pytest.raises(ValidationError):
        PaymentCreate(
            patient_id=1,
            due_date=date(2031, 1, 2),
            competence_date=date(2031, 1, 1),
            amount_cents=0,
        )
    with pytest.raises(ValidationError):
        PaymentCreate(
            patient_id=1,
            due_date=date(2031, 1, 2),
            competence_date=date(2031, 1, 1),
            amount_cents=10.5,
        )


def test_ac003_and_ac004_schema_has_explicit_regime_lifecycle_and_version_fields():
    columns = _columns("payments")

    assert {
        "competence_date",
        "paid_at",
        "status",
        "version",
        "created_at",
        "updated_at",
        "canceled_at",
        "reversed_at",
    } <= set(columns)
    assert "overdue" not in columns


def test_ac005_and_ac009_schema_has_append_only_history_and_controlled_categories():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())

    assert {"financial_events", "expense_categories"} <= tables
    expense_columns = _columns("expenses")
    assert "category_id" in expense_columns
    assert "category" not in expense_columns


def test_ac007_appointment_link_remains_nullable_and_never_cascades_delete():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    columns = {item["name"]: item for item in inspect(engine).get_columns("payments")}
    foreign_keys = inspect(engine).get_foreign_keys("payments")

    assert columns["appointment_id"]["nullable"] is True
    appointment_fk = next(
        item for item in foreign_keys if item["constrained_columns"] == ["appointment_id"]
    )
    assert appointment_fk.get("options", {}).get("ondelete") != "CASCADE"


def test_ac001_database_constraints_reject_non_positive_amount_and_invalid_status():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, future=True)
    payment_model = finance.Payment
    patient_model = patient.Patient

    with sessions() as db:
        person = patient_model(full_name="Pessoa Sintetica", active=True)
        db.add(person)
        db.commit()
        db.add(
            payment_model(
                patient_id=person.id,
                amount_cents=0,
                competence_date=date(2031, 1, 1),
                due_date=date(2031, 1, 2),
                status="invented",
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
