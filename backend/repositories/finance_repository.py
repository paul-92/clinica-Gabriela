from sqlalchemy import update

from backend.models.finance import Expense, ExpenseCategory, FinancialEvent, Payment
from backend.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Payment)

    def list_filtered(self, start, end, regime, status=None, patient_id=None):
        query = self.db.query(Payment)
        period_column = Payment.paid_at if regime == "cash" else Payment.competence_date
        query = query.filter(period_column >= start, period_column < end)
        if status:
            query = query.filter(Payment.status == status)
        if patient_id is not None:
            query = query.filter(Payment.patient_id == patient_id)
        return query.order_by(period_column.desc(), Payment.id.desc()).all()

    def get(self, payment_id):
        return self.db.get(Payment, payment_id)

    def compare_and_update(self, payment_id, expected_version, values):
        statement = (
            update(Payment)
            .where(Payment.id == payment_id, Payment.version == expected_version)
            .values(**values, version=Payment.version + 1)
        )
        return self.db.execute(statement).rowcount


class ExpenseRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Expense)

    def list_filtered(self, start, end, regime, status=None, category_id=None):
        period_column = Expense.expense_date if regime == "cash" else Expense.competence_date
        query = self.db.query(Expense).filter(period_column >= start, period_column < end)
        if status:
            query = query.filter(Expense.status == status)
        if category_id is not None:
            query = query.filter(Expense.category_id == category_id)
        return query.order_by(period_column.desc(), Expense.id.desc()).all()

    def get(self, expense_id):
        return self.db.get(Expense, expense_id)

    def compare_and_update(self, expense_id, expected_version, values):
        statement = (
            update(Expense)
            .where(Expense.id == expense_id, Expense.version == expected_version)
            .values(**values, version=Expense.version + 1)
        )
        return self.db.execute(statement).rowcount


class ExpenseCategoryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, ExpenseCategory)

    def list_all(self, include_inactive=False):
        query = self.db.query(ExpenseCategory)
        if not include_inactive:
            query = query.filter(ExpenseCategory.active.is_(True))
        return query.order_by(ExpenseCategory.name, ExpenseCategory.id).all()

    def get(self, category_id):
        return self.db.get(ExpenseCategory, category_id)

    def compare_and_update(self, category_id, expected_version, values):
        statement = (
            update(ExpenseCategory)
            .where(ExpenseCategory.id == category_id, ExpenseCategory.version == expected_version)
            .values(**values, version=ExpenseCategory.version + 1)
        )
        return self.db.execute(statement).rowcount


class FinancialEventRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, FinancialEvent)

    def list_for(self, resource_type, resource_id):
        return (
            self.db.query(FinancialEvent)
            .filter(
                FinancialEvent.resource_type == resource_type,
                FinancialEvent.resource_id == resource_id,
            )
            .order_by(FinancialEvent.id)
            .all()
        )
