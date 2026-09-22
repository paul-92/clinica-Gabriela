from datetime import date, datetime

from pydantic import ConfigDict, Field, StrictInt, field_validator

from backend.schemas.common import ORMBase


class FinanceInput(ORMBase):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PaymentBase(FinanceInput):
    patient_id: int
    appointment_id: int | None = None
    competence_date: date
    due_date: date
    amount_cents: StrictInt = Field(gt=0)
    payment_method: str = ""
    description: str = ""


class PaymentCreate(PaymentBase):
    @field_validator("payment_method", "description")
    @classmethod
    def strip_text(cls, value):
        return value.strip()


class PaymentUpdate(FinanceInput):
    appointment_id: int | None = None
    competence_date: date | None = None
    due_date: date | None = None
    amount_cents: StrictInt | None = Field(default=None, gt=0)
    payment_method: str | None = None
    description: str | None = None


class PaymentRead(PaymentBase):
    id: int
    paid_at: date | None
    status: str
    version: int
    overdue: bool = False


class PaymentAction(FinanceInput):
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Motivo obrigatorio.")
        return value


class PaymentSettlement(FinanceInput):
    paid_at: date
    payment_method: str = Field(min_length=1, max_length=50)

    @field_validator("payment_method")
    @classmethod
    def method_not_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Forma de pagamento obrigatoria.")
        return value


class ExpenseBase(FinanceInput):
    description: str
    amount_cents: StrictInt = Field(gt=0)
    expense_date: date
    competence_date: date
    category_id: int


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: int
    status: str
    version: int
    category_name: str = ""


class ExpenseAction(PaymentAction):
    pass


class ExpenseCategoryCreate(FinanceInput):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Nome obrigatorio.")
        return value


class ExpenseCategoryUpdate(FinanceInput):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    active: bool | None = None


class ExpenseCategoryRead(ORMBase):
    id: int
    name: str
    active: bool
    version: int


class FinancialEventRead(ORMBase):
    id: int
    resource_type: str
    resource_id: int
    actor_user_id: int | None
    event_type: str
    from_status: str | None
    to_status: str | None
    reason: str
    created_at: datetime


class FinanceSummary(ORMBase):
    regime: str
    start: date
    end: date
    income_cents: int
    receivable_cents: int
    expense_cents: int
    balance_cents: int
