from backend.models.finance import Expense, Payment
from backend.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Payment)

    def list_recent(self):
        return self.db.query(Payment).order_by(Payment.due_date.desc()).all()


class ExpenseRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Expense)

    def list_recent(self):
        return self.db.query(Expense).order_by(Expense.expense_date.desc()).all()
