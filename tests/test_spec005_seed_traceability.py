from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.database.seed import seed_database
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
from backend.models.user import User


def _fk_on(connection, _record):
    connection.execute("PRAGMA foreign_keys=ON")


def test_f002_canonical_seed_uses_financial_service_traceability(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'seed.db'}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", _fk_on)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    try:
        seed_database(sessions)
        with sessions() as session:
            actor = session.query(User).filter_by(username="__seed_finance_actor__").one()
            category = session.query(ExpenseCategory).one()
            payment = session.query(Payment).one()
            expense = session.query(Expense).one()
            events = session.query(FinancialEvent).order_by(FinancialEvent.id).all()

            assert actor.active is False
            assert actor.role == "admin"
            assert {category.created_by_user_id, payment.created_by_user_id, expense.created_by_user_id} == {actor.id}
            assert [(item.resource_type, item.resource_id, item.actor_user_id, item.event_type) for item in events] == [
                ("expense_category", category.id, actor.id, "created"),
                ("payment", payment.id, actor.id, "created"),
                ("expense", expense.id, actor.id, "created"),
            ]
            assert all(item.actor_user_id is not None for item in events)

        seed_database(sessions)
        with sessions() as session:
            assert session.query(User).filter_by(username="__seed_finance_actor__").count() == 1
            assert session.query(ExpenseCategory).count() == 1
            assert session.query(Payment).count() == 1
            assert session.query(Expense).count() == 1
            assert session.query(FinancialEvent).count() == 3
    finally:
        engine.dispose()
