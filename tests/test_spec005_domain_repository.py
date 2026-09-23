from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
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
from backend.models.finance import Expense, ExpenseCategory, FinancialEvent, Payment
from backend.models.appointment import Appointment
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.user import User
from backend.services.finance_service import FinanceService


def _fk_on(connection, _record):
    connection.execute("PRAGMA foreign_keys=ON")


@pytest.fixture
def finance_db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'finance.db'}", future=True, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _fk_on)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with sessions() as db:
        db.add_all(
            [
                Patient(id=101, full_name="Pessoa Sintetica", active=True),
                Psychologist(
                    id=301, full_name="Profissional Sintetico", crp_region="00", crp_number="00000",
                    crp_status="apt", active=True,
                ),
                User(id=201, name="Admin Sintetico", username="admin_sintetico", password_hash="x", role="admin", active=True),
                User(id=202, name="Recepcao Sintetica", username="recepcao_sintetica", password_hash="x", role="reception", active=True),
                User(id=203, name="Psicologo Sintetico", username="psicologo_sintetico", password_hash="x", role="psychologist", active=True),
            ]
        )
        db.commit()
        db.add(
            Appointment(
                id=401, patient_id=101, psychologist_id=301,
                scheduled_at=datetime(2031, 2, 10, 10, 0), status="scheduled",
            )
        )
        db.commit()
    try:
        yield sessions
    finally:
        engine.dispose()


def actor(role):
    return SimpleNamespace(id={"admin": 201, "reception": 202, "psychologist": 203}[role], role=role)


def charge(amount_cents=10, competence=(2031, 1), due=date(2031, 2, 5)):
    return {
        "patient_id": 101,
        "appointment_id": None,
        "competence_year": competence[0],
        "competence_month": competence[1],
        "due_date": due,
        "amount_cents": amount_cents,
        "payment_method": "",
        "description": "Cobranca sintetica",
    }


def test_ac002_exact_cent_arithmetic_and_ac003_period_boundaries(finance_db):
    with finance_db() as db:
        service = FinanceService(db)
        first = service.create_payment(charge(10), actor("reception"))
        second = service.create_payment(charge(20, competence=(2031, 2)), actor("reception"))
        service.register_payment(first["id"], {"paid_at": date(2031, 2, 1), "payment_method": "Pix"}, 1, actor("reception"))
        service.register_payment(second["id"], {"paid_at": date(2031, 3, 1), "payment_method": "Pix"}, 1, actor("reception"))

        january_accrual = service.summary(
            None, None, "accrual", actor("admin"), 2031, 1, 2031, 2
        )
        february_accrual = service.summary(
            None, None, "accrual", actor("admin"), 2031, 2, 2031, 3
        )
        february_cash = service.summary(date(2031, 2, 1), date(2031, 3, 1), "cash", actor("admin"))
        march_cash = service.summary(date(2031, 3, 1), date(2031, 4, 1), "cash", actor("admin"))

        assert january_accrual["income_cents"] == 10
        assert february_accrual["income_cents"] == 20
        assert february_cash["income_cents"] == 10
        assert march_cash["income_cents"] == 20
        assert january_accrual["income_cents"] + february_accrual["income_cents"] == 30


def test_ac004_overdue_is_derived_and_lifecycle_is_explicit(finance_db):
    with finance_db() as db:
        service = FinanceService(db)
        item = service.create_payment(charge(due=date(2031, 1, 10)), actor("reception"))
        listed = service.list_payments(
            None, None, "accrual", reference_date=date(2031, 1, 11), actor=actor("reception"),
            start_year=2031, start_month=1, end_year=2031, end_month=2,
        )
        assert listed[0]["overdue"] is True
        assert db.get(Payment, item["id"]).status == "pending"
        assert not hasattr(db.get(Payment, item["id"]), "overdue")

        paid = service.register_payment(item["id"], {"paid_at": date(2031, 1, 12), "payment_method": "Pix"}, 1, actor("reception"))
        assert paid["status"] == "paid"
        with pytest.raises(HTTPException) as invalid:
            service.cancel_payment(item["id"], "invalido", 2, actor("reception"))
        assert invalid.value.status_code == 409
        reversed_item = service.reverse_payment(item["id"], "estorno sintetico", 2, actor("admin"))
        assert reversed_item["status"] == "reversed"
        assert db.query(FinancialEvent).filter_by(resource_type="payment", resource_id=item["id"]).count() == 3


def test_ac005_cancellation_preserves_original_and_physical_delete_is_blocked(finance_db):
    with finance_db() as db:
        service = FinanceService(db)
        item = service.create_payment(charge(1234), actor("reception"))
        canceled = service.cancel_payment(item["id"], "cancelamento sintetico", 1, actor("reception"))
        persisted = db.get(Payment, item["id"])

        assert canceled["status"] == "canceled"
        assert persisted.amount_cents == 1234
        assert persisted.cancellation_reason == "cancelamento sintetico"
        db.delete(persisted)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_ac006_partial_multiple_settlement_and_installments_are_rejected(finance_db):
    with finance_db() as db:
        service = FinanceService(db)
        for forbidden in (
            {"partial_amount_cents": 5},
            {"installments": 2},
            {"settlements": [{"amount_cents": 10}]},
        ):
            with pytest.raises(HTTPException) as failure:
                service.create_payment({**charge(), **forbidden}, actor("reception"))
            assert failure.value.status_code == 422

        item = service.create_payment(charge(), actor("reception"))
        service.register_payment(item["id"], {"paid_at": date(2031, 2, 1), "payment_method": "Pix"}, 1, actor("reception"))
        with pytest.raises(HTTPException) as duplicate:
            service.register_payment(item["id"], {"paid_at": date(2031, 2, 2), "payment_method": "Pix"}, 2, actor("reception"))
        assert duplicate.value.status_code == 409


def test_ac007_appointment_is_nullable_not_inferred_and_agenda_has_no_billing_side_effect(finance_db):
    with finance_db() as db:
        service = FinanceService(db)
        item = service.create_payment(charge(), actor("reception"))
        assert item["appointment_id"] is None
        before = db.query(Payment).count()
        from backend.services.appointment_service import AppointmentService
        AppointmentService(db).transition(401, "canceled", actor("reception"), 1, "cancelamento sintetico")
        assert db.query(Payment).count() == before
        assert db.get(Payment, item["id"]).appointment_id is None


def test_ac009_controlled_categories_and_expense_history(finance_db):
    with finance_db() as db:
        service = FinanceService(db)
        with pytest.raises(HTTPException) as denied:
            service.create_category({"name": "Operacional"}, actor("reception"))
        assert denied.value.status_code == 403
        category = service.create_category({"name": "Operacional"}, actor("admin"))
        expense = service.create_expense(
            {
                "description": "Despesa sintetica",
                "amount_cents": 250,
                "expense_date": date(2031, 2, 3),
                "competence_year": 2031,
                "competence_month": 2,
                "category_id": category.id,
            },
            actor("admin"),
        )
        canceled = service.cancel_expense(expense["id"], "cancelamento sintetico", 1, actor("admin"))
        assert canceled["status"] == "canceled"
        assert db.get(Expense, expense["id"]).amount_cents == 250
        assert db.query(FinancialEvent).filter_by(resource_type="expense", resource_id=expense["id"]).count() == 2


def test_ac010_stale_competing_update_fails_without_lost_update(finance_db):
    first_session = finance_db()
    second_session = finance_db()
    try:
        created = FinanceService(first_session).create_payment(charge(500), actor("reception"))
        stale_copy = second_session.get(Payment, created["id"])
        assert stale_copy.version == 1
        updated = FinanceService(first_session).update_payment(
            created["id"], {"description": "primeira alteracao"}, 1, actor("reception")
        )
        assert updated["version"] == 2
        with pytest.raises(HTTPException) as stale:
            FinanceService(second_session).update_payment(
                created["id"], {"description": "alteracao perdida"}, 1, actor("reception")
            )
        assert stale.value.status_code == 412
        second_session.expire_all()
        assert second_session.get(Payment, created["id"]).description == "primeira alteracao"
        assert second_session.query(FinancialEvent).filter_by(resource_type="payment", resource_id=created["id"]).count() == 2
    finally:
        first_session.close()
        second_session.close()
