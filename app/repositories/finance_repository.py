from app.models.finance import Expense, Payment


class FinanceRepository:
    def __init__(self, session):
        self.session = session

    def payments(self):
        return self.session.query(Payment).order_by(Payment.due_date.desc()).all()

    def expenses(self):
        return self.session.query(Expense).order_by(Expense.expense_date.desc()).all()
