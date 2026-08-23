from datetime import date

from backend.schemas.common import ORMBase


class PaymentBase(ORMBase):
    patient_id: int
    appointment_id: int | None = None
    due_date: date
    paid_at: date | None = None
    amount: float
    status: str = "pending"
    payment_method: str = ""
    description: str = ""


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(ORMBase):
    appointment_id: int | None = None
    due_date: date | None = None
    paid_at: date | None = None
    amount: float | None = None
    status: str | None = None
    payment_method: str | None = None
    description: str | None = None


class PaymentRead(PaymentBase):
    id: int


class ExpenseBase(ORMBase):
    description: str
    amount: float
    expense_date: date
    category: str = ""


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: int


class FinanceSummary(ORMBase):
    paid: float
    pending: float
    expenses: float
    balance: float
