from app.repositories.finance_repository import FinanceRepository


class FinanceService:
    def __init__(self, session):
        self.repository = FinanceRepository(session)

    def monthly_summary(self):
        payments = self.repository.payments()
        expenses = self.repository.expenses()
        paid = sum(item.amount for item in payments if item.status == "paid")
        pending = sum(item.amount for item in payments if item.status == "pending")
        expense_total = sum(item.amount for item in expenses)
        return {
            "paid": paid,
            "pending": pending,
            "expenses": expense_total,
            "balance": paid - expense_total,
        }
