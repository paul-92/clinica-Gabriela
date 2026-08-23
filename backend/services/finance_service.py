from backend.repositories.finance_repository import ExpenseRepository, PaymentRepository


class FinanceService:
    def __init__(self, db):
        self.payments = PaymentRepository(db)
        self.expenses = ExpenseRepository(db)

    def list_payments(self):
        return self.payments.list_recent()

    def create_payment(self, data):
        return self.payments.create(data)

    def list_expenses(self):
        return self.expenses.list_recent()

    def create_expense(self, data):
        return self.expenses.create(data)

    def summary(self):
        payments = self.list_payments()
        expenses = self.list_expenses()
        paid = sum(item.amount for item in payments if item.status == "paid")
        pending = sum(item.amount for item in payments if item.status == "pending")
        expense_total = sum(item.amount for item in expenses)
        return {
            "paid": paid,
            "pending": pending,
            "expenses": expense_total,
            "balance": paid - expense_total,
        }
