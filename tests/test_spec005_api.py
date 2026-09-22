from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.api.routes import finance
from backend.api.routes.auth import get_current_user
from backend.database.session import Base, get_db
from backend.models import (  # noqa: F401
    appointment,
    clinical_record,
    patient,
    psychologist,
    settings,
    user,
)
from backend.models.patient import Patient
from backend.models.user import User


def _fk_on(connection, _record):
    connection.execute("PRAGMA foreign_keys=ON")


@pytest.fixture
def api_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}", future=True, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _fk_on)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with sessions() as db:
        db.add(Patient(id=101, full_name="Pessoa Sintetica", active=True))
        db.add_all(
            [
                User(id=201, name="Admin", username="admin_api", password_hash="x", role="admin", active=True),
                User(id=202, name="Recepcao", username="reception_api", password_hash="x", role="reception", active=True),
                User(id=203, name="Psicologo", username="psychologist_api", password_hash="x", role="psychologist", active=True),
            ]
        )
        db.commit()

    def factory(role=None):
        app = FastAPI()
        app.include_router(finance.router)

        def database():
            with sessions() as db:
                yield db

        app.dependency_overrides[get_db] = database
        if role:
            app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
                id={"admin": 201, "reception": 202, "psychologist": 203}[role], role=role
            )
        return TestClient(app)

    try:
        yield factory
    finally:
        engine.dispose()


def _charge(amount_cents=1000):
    return {
        "patient_id": 101,
        "appointment_id": None,
        "competence_date": "2031-02-01",
        "due_date": "2031-02-10",
        "amount_cents": amount_cents,
        "payment_method": "",
        "description": "Cobranca sintetica",
    }


def test_ac008_missing_auth_is_401_and_psychologist_is_403(api_factory):
    with api_factory() as anonymous:
        assert anonymous.get("/finance/summary?start=2031-02-01&end=2031-03-01").status_code == 401
    with api_factory("psychologist") as psychologist:
        denied = psychologist.get("/finance/summary?start=2031-02-01&end=2031-03-01")
        assert denied.status_code == 403
        assert "traceback" not in denied.text.lower()


def test_ac008_reception_operates_charges_but_not_reversal_or_expenses(api_factory):
    with api_factory("reception") as reception:
        created = reception.post("/finance/payments", json=_charge())
        assert created.status_code == 201
        assert created.json()["amount_cents"] == 1000
        assert created.headers["etag"] == '"1"'
        payment_id = created.json()["id"]

        paid = reception.post(
            f"/finance/payments/{payment_id}/pay",
            json={"paid_at": "2031-02-12", "payment_method": "Pix"},
            headers={"If-Match": '"1"'},
        )
        assert paid.status_code == 200
        assert paid.json()["status"] == "paid"
        assert reception.post(
            f"/finance/payments/{payment_id}/reverse",
            json={"reason": "negado"},
            headers={"If-Match": '"2"'},
        ).status_code == 403
        assert reception.post(
            "/finance/expenses",
            json={
                "description": "Despesa sintetica",
                "amount_cents": 100,
                "expense_date": "2031-02-02",
                "competence_date": "2031-02-01",
                "category_id": 1,
            },
        ).status_code == 403


def test_ac008_admin_category_expense_and_reversal_matrix(api_factory):
    with api_factory("admin") as admin:
        category = admin.post("/finance/categories", json={"name": "Operacional"})
        assert category.status_code == 201
        expense = admin.post(
            "/finance/expenses",
            json={
                "description": "Despesa sintetica",
                "amount_cents": 200,
                "expense_date": "2031-02-02",
                "competence_date": "2031-02-01",
                "category_id": category.json()["id"],
            },
        )
        assert expense.status_code == 201
        canceled = admin.post(
            f"/finance/expenses/{expense.json()['id']}/cancel",
            json={"reason": "cancelamento sintetico"},
            headers={"If-Match": '"1"'},
        )
        assert canceled.status_code == 200
        assert canceled.json()["status"] == "canceled"


def test_ac001_ac006_and_period_contract_return_422(api_factory):
    with api_factory("admin") as admin:
        for invalid in (
            _charge(0),
            _charge(10.5),
            {**_charge(), "installments": 2},
            {**_charge(), "partial_amount_cents": 5},
        ):
            response = admin.post("/finance/payments", json=invalid)
            assert response.status_code == 422
            assert "traceback" not in response.text.lower()
        assert admin.get("/finance/summary").status_code == 422
        assert admin.get("/finance/summary?start=2031-03-01&end=2031-02-01").status_code == 422


def test_ac010_etag_stale_version_is_412_and_conflict_is_409(api_factory):
    with api_factory("admin") as admin:
        created = admin.post("/finance/payments", json=_charge()).json()
        payment_id = created["id"]
        updated = admin.patch(
            f"/finance/payments/{payment_id}",
            json={"description": "alterado"},
            headers={"If-Match": '"1"'},
        )
        assert updated.status_code == 200
        stale = admin.patch(
            f"/finance/payments/{payment_id}",
            json={"description": "perdido"},
            headers={"If-Match": '"1"'},
        )
        assert stale.status_code == 412
        paid = admin.post(
            f"/finance/payments/{payment_id}/pay",
            json={"paid_at": "2031-02-12", "payment_method": "Pix"},
            headers={"If-Match": '"2"'},
        )
        assert paid.status_code == 200
        conflict = admin.post(
            f"/finance/payments/{payment_id}/pay",
            json={"paid_at": "2031-02-13", "payment_method": "Pix"},
            headers={"If-Match": '"3"'},
        )
        assert conflict.status_code == 409
        missing = admin.get("/finance/payments/999")
        assert missing.status_code == 404


def test_ac003_summary_uses_explicit_half_open_period(api_factory):
    with api_factory("admin") as admin:
        first = admin.post("/finance/payments", json=_charge(10)).json()
        second_payload = {**_charge(20), "competence_date": "2031-03-01"}
        second = admin.post("/finance/payments", json=second_payload).json()
        admin.post(
            f"/finance/payments/{first['id']}/pay",
            json={"paid_at": "2031-02-28", "payment_method": "Pix"},
            headers={"If-Match": '"1"'},
        )
        admin.post(
            f"/finance/payments/{second['id']}/pay",
            json={"paid_at": "2031-03-01", "payment_method": "Pix"},
            headers={"If-Match": '"1"'},
        )
        cash = admin.get("/finance/summary?start=2031-02-01&end=2031-03-01&regime=cash")
        accrual = admin.get("/finance/summary?start=2031-02-01&end=2031-03-01&regime=accrual")
        assert cash.json()["income_cents"] == 10
        assert accrual.json()["income_cents"] == 10
        assert cash.json()["regime"] == "cash"
