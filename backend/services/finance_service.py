from datetime import date, datetime, timezone

from backend.repositories.finance_repository import (
    ExpenseCategoryRepository,
    ExpenseRepository,
    FinancialEventRepository,
    PaymentRepository,
)
from backend.models.appointment import Appointment
from backend.models.finance import Expense, ExpenseCategory, FinancialEvent, Payment
from backend.models.patient import Patient
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from backend.services.errors import translate_integrity_error


class FinanceService:
    def __init__(self, db):
        self.db = db
        self.payments = PaymentRepository(db)
        self.expenses = ExpenseRepository(db)
        self.categories = ExpenseCategoryRepository(db)
        self.events = FinancialEventRepository(db)

    @staticmethod
    def _authorize(actor, capability):
        if actor is None:
            raise HTTPException(401, "Autenticacao obrigatoria.")
        if actor.role == "psychologist":
            raise HTTPException(403, "Modulo financeiro indisponivel para este perfil.")
        if actor.role not in {"admin", "reception"}:
            raise HTTPException(403, "Perfil sem permissao financeira.")
        if capability in {"reverse", "expense_mutation", "category_mutation", "audit"} and actor.role != "admin":
            raise HTTPException(403, "Operacao financeira exclusiva de administrador.")

    @staticmethod
    def _validate_period(start, end, regime, start_year=None, start_month=None, end_year=None, end_month=None):
        if regime not in {"cash", "accrual"}:
            raise HTTPException(422, "Regime financeiro invalido.")
        if regime == "cash":
            if any(value is not None for value in (start_year, start_month, end_year, end_month)):
                raise HTTPException(422, "Caixa usa somente limites de data start/end.")
            if start is None or end is None or start >= end:
                raise HTTPException(422, "Periodo de caixa [start,end) invalido.")
            return start, end, start.isoformat(), end.isoformat()
        if start is not None or end is not None:
            raise HTTPException(422, "Competencia usa somente limites mensais de ano e mes.")
        values = (start_year, start_month, end_year, end_month)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise HTTPException(422, "Periodo mensal de competencia incompleto.")
        if not (1 <= start_year <= 9999 and 1 <= end_year <= 9999):
            raise HTTPException(422, "Ano da competencia invalido.")
        if not (1 <= start_month <= 12 and 1 <= end_month <= 12):
            raise HTTPException(422, "Mes da competencia invalido.")
        period_start = (start_year, start_month)
        period_end = (end_year, end_month)
        if period_start >= period_end:
            raise HTTPException(422, "Periodo mensal [start_month,end_month) invalido.")
        return period_start, period_end, f"{start_year:04d}-{start_month:02d}", f"{end_year:04d}-{end_month:02d}"

    @staticmethod
    def _validate_competence(data, required):
        if "competence_date" in data:
            raise HTTPException(422, "competence_date nao integra o contrato canonico.")
        has_year = "competence_year" in data
        has_month = "competence_month" in data
        if has_year != has_month or (required and not has_year):
            raise HTTPException(422, "Ano e mes da competencia devem ser informados juntos.")
        if not has_year:
            return
        year = data["competence_year"]
        month = data["competence_month"]
        if isinstance(year, bool) or not isinstance(year, int) or not 1 <= year <= 9999:
            raise HTTPException(422, "Ano da competencia invalido.")
        if isinstance(month, bool) or not isinstance(month, int) or not 1 <= month <= 12:
            raise HTTPException(422, "Mes da competencia invalido.")

    @staticmethod
    def _precondition(item, expected_version):
        if expected_version is None:
            raise HTTPException(428, "If-Match obrigatorio.")
        if item.version != expected_version:
            raise HTTPException(412, "Versao do recurso desatualizada.")

    @staticmethod
    def _event(resource_type, resource_id, actor, event_type, from_status=None, to_status=None, reason=""):
        return FinancialEvent(
            resource_type=resource_type,
            resource_id=resource_id,
            actor_user_id=actor.id if actor is not None else None,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
        )

    def _commit(self):
        try:
            self.db.commit()
        except IntegrityError as exc:
            translate_integrity_error(self.db, exc)
        except OperationalError as exc:
            self.db.rollback()
            raise HTTPException(409, "Financeiro temporariamente indisponivel; tente novamente.") from exc

    def list_payments(self, start, end, regime="cash", status=None, patient_id=None, reference_date=None, actor=None,
                      start_year=None, start_month=None, end_year=None, end_month=None):
        self._authorize(actor, "view")
        period_start, period_end, _, _ = self._validate_period(
            start, end, regime, start_year, start_month, end_year, end_month
        )
        persisted_status = "pending" if status == "overdue" else status
        if persisted_status is not None and persisted_status not in {"pending", "paid", "canceled", "reversed"}:
            raise HTTPException(422, "Filtro de status invalido.")
        items = self.payments.list_filtered(period_start, period_end, regime, persisted_status, patient_id)
        reference = reference_date or date.today()
        result = [self._payment_payload(item, reference) for item in items]
        if status == "overdue":
            result = [item for item in result if item["overdue"]]
        return result

    def get_payment(self, payment_id, reference_date=None, actor=None):
        self._authorize(actor, "view")
        item = self.payments.get(payment_id)
        if item is None:
            raise HTTPException(404, "Cobranca nao encontrada.")
        return self._payment_payload(item, reference_date or date.today())

    @staticmethod
    def _payment_payload(item, reference_date):
        return {
            "id": item.id,
            "patient_id": item.patient_id,
            "appointment_id": item.appointment_id,
            "competence_year": item.competence_year,
            "competence_month": item.competence_month,
            "competence_period": f"{item.competence_year:04d}-{item.competence_month:02d}",
            "due_date": item.due_date,
            "paid_at": item.paid_at,
            "amount_cents": item.amount_cents,
            "status": item.status,
            "payment_method": item.payment_method,
            "description": item.description,
            "version": item.version,
            "overdue": item.status == "pending" and item.due_date < reference_date,
        }

    def create_payment(self, data, actor=None):
        self._authorize(actor, "create")
        self._validate_competence(data, required=True)
        if any(key in data for key in ("paid_at", "status", "partial_amount_cents", "installments", "settlements")):
            raise HTTPException(422, "Representacao de liquidacao nao suportada.")
        patient = self.payments.db.get(Patient, data["patient_id"])
        if patient is None:
            raise HTTPException(status_code=404, detail="Paciente nao encontrado.")
        if not patient.active:
            raise HTTPException(status_code=409, detail="Paciente inativo para novos fatos financeiros.")
        if data.get("appointment_id") is not None:
            appointment = self.payments.db.get(Appointment, data["appointment_id"])
            if appointment is None:
                raise HTTPException(status_code=404, detail="Atendimento nao encontrado.")
            if appointment.patient_id != patient.id:
                raise HTTPException(status_code=409, detail="Atendimento nao pertence ao paciente informado.")
        item = Payment(**data, status="pending", created_by_user_id=actor.id)
        self.db.add(item)
        try:
            self.db.flush()
            self.db.add(self._event("payment", item.id, actor, "created", to_status="pending"))
            self._commit()
            self.db.refresh(item)
            return self._payment_payload(item, date.today())
        except Exception:
            if self.db.in_transaction():
                self.db.rollback()
            raise

    def update_payment(self, payment_id, data, expected_version, actor=None):
        self._authorize(actor, "update")
        self._validate_competence(data, required=False)
        item = self.payments.get(payment_id)
        if item is None:
            raise HTTPException(404, "Cobranca nao encontrada.")
        self._precondition(item, expected_version)
        if item.status != "pending":
            raise HTTPException(409, "Somente cobranca pendente pode ser alterada.")
        if "appointment_id" in data and data["appointment_id"] is not None:
            appointment = self.db.get(Appointment, data["appointment_id"])
            if appointment is None:
                raise HTTPException(404, "Atendimento nao encontrado.")
            if appointment.patient_id != item.patient_id:
                raise HTTPException(409, "Atendimento nao pertence ao paciente informado.")
        if not self.payments.compare_and_update(payment_id, expected_version, data):
            self.db.rollback()
            raise HTTPException(412, "Versao do recurso desatualizada.")
        self.db.add(self._event("payment", payment_id, actor, "updated", "pending", "pending"))
        self._commit()
        return self.get_payment(payment_id, actor=actor)

    def register_payment(self, payment_id, data, expected_version, actor=None):
        self._authorize(actor, "settle")
        item = self.payments.get(payment_id)
        if item is None:
            raise HTTPException(404, "Cobranca nao encontrada.")
        self._precondition(item, expected_version)
        if item.status != "pending":
            raise HTTPException(409, "Somente cobranca pendente pode ser paga integralmente.")
        values = {"status": "paid", "paid_at": data["paid_at"], "payment_method": data["payment_method"]}
        if not self.payments.compare_and_update(payment_id, expected_version, values):
            self.db.rollback()
            raise HTTPException(412, "Versao do recurso desatualizada.")
        self.db.add(self._event("payment", payment_id, actor, "paid", "pending", "paid"))
        self._commit()
        return self.get_payment(payment_id, actor=actor)

    def cancel_payment(self, payment_id, reason, expected_version, actor=None):
        self._authorize(actor, "cancel")
        item = self.payments.get(payment_id)
        if item is None:
            raise HTTPException(404, "Cobranca nao encontrada.")
        self._precondition(item, expected_version)
        if item.status != "pending":
            raise HTTPException(409, "Somente cobranca pendente pode ser cancelada.")
        values = {"status": "canceled", "canceled_at": datetime.now(timezone.utc), "canceled_by_user_id": actor.id, "cancellation_reason": reason}
        if not self.payments.compare_and_update(payment_id, expected_version, values):
            self.db.rollback()
            raise HTTPException(412, "Versao do recurso desatualizada.")
        self.db.add(self._event("payment", payment_id, actor, "canceled", "pending", "canceled", reason))
        self._commit()
        return self.get_payment(payment_id, actor=actor)

    def reverse_payment(self, payment_id, reason, expected_version, actor=None):
        self._authorize(actor, "reverse")
        item = self.payments.get(payment_id)
        if item is None:
            raise HTTPException(404, "Cobranca nao encontrada.")
        self._precondition(item, expected_version)
        if item.status != "paid":
            raise HTTPException(409, "Somente cobranca paga pode ser estornada.")
        values = {"status": "reversed", "reversed_at": datetime.now(timezone.utc), "reversed_by_user_id": actor.id, "reversal_reason": reason}
        if not self.payments.compare_and_update(payment_id, expected_version, values):
            self.db.rollback()
            raise HTTPException(412, "Versao do recurso desatualizada.")
        self.db.add(self._event("payment", payment_id, actor, "reversed", "paid", "reversed", reason))
        self._commit()
        return self.get_payment(payment_id, actor=actor)

    def list_expenses(self, start, end, regime="cash", status=None, category_id=None, actor=None,
                      start_year=None, start_month=None, end_year=None, end_month=None):
        self._authorize(actor, "view")
        period_start, period_end, _, _ = self._validate_period(
            start, end, regime, start_year, start_month, end_year, end_month
        )
        if status is not None and status not in {"active", "canceled"}:
            raise HTTPException(422, "Filtro de status de despesa invalido.")
        return [
            self._expense_payload(item)
            for item in self.expenses.list_filtered(period_start, period_end, regime, status, category_id)
        ]

    @staticmethod
    def _expense_payload(item):
        return {
            "id": item.id,
            "description": item.description,
            "amount_cents": item.amount_cents,
            "expense_date": item.expense_date,
            "competence_year": item.competence_year,
            "competence_month": item.competence_month,
            "competence_period": f"{item.competence_year:04d}-{item.competence_month:02d}",
            "category_id": item.category_id,
            "category_name": item.category.name if item.category else "",
            "status": item.status,
            "version": item.version,
        }

    def create_expense(self, data, actor=None):
        self._authorize(actor, "expense_mutation")
        self._validate_competence(data, required=True)
        category = self.categories.get(data["category_id"])
        if category is None:
            raise HTTPException(404, "Categoria de despesa nao encontrada.")
        if not category.active:
            raise HTTPException(409, "Categoria de despesa inativa.")
        item = Expense(**data, status="active", created_by_user_id=actor.id)
        self.db.add(item)
        try:
            self.db.flush()
            self.db.add(self._event("expense", item.id, actor, "created", to_status="active"))
            self._commit()
            self.db.refresh(item)
            return self._expense_payload(item)
        except Exception:
            if self.db.in_transaction():
                self.db.rollback()
            raise

    def cancel_expense(self, expense_id, reason, expected_version, actor=None):
        self._authorize(actor, "expense_mutation")
        item = self.expenses.get(expense_id)
        if item is None:
            raise HTTPException(404, "Despesa nao encontrada.")
        self._precondition(item, expected_version)
        if item.status != "active":
            raise HTTPException(409, "Despesa ja esta cancelada.")
        values = {"status": "canceled", "canceled_at": datetime.now(timezone.utc), "canceled_by_user_id": actor.id, "cancellation_reason": reason}
        if not self.expenses.compare_and_update(expense_id, expected_version, values):
            self.db.rollback()
            raise HTTPException(412, "Versao do recurso desatualizada.")
        self.db.add(self._event("expense", expense_id, actor, "canceled", "active", "canceled", reason))
        self._commit()
        return self._expense_payload(self.expenses.get(expense_id))

    def list_categories(self, include_inactive=False, actor=None):
        self._authorize(actor, "view")
        return self.categories.list_all(include_inactive and actor.role == "admin")

    def create_category(self, data, actor=None):
        self._authorize(actor, "category_mutation")
        item = ExpenseCategory(**data, created_by_user_id=actor.id)
        self.db.add(item)
        try:
            self.db.flush()
            self.db.add(self._event("expense_category", item.id, actor, "created"))
            self._commit()
            self.db.refresh(item)
            return item
        except Exception:
            if self.db.in_transaction():
                self.db.rollback()
            raise

    def update_category(self, category_id, data, expected_version, actor=None):
        self._authorize(actor, "category_mutation")
        item = self.categories.get(category_id)
        if item is None:
            raise HTTPException(404, "Categoria de despesa nao encontrada.")
        self._precondition(item, expected_version)
        if not self.categories.compare_and_update(category_id, expected_version, data):
            self.db.rollback()
            raise HTTPException(412, "Versao do recurso desatualizada.")
        self.db.add(self._event("expense_category", category_id, actor, "updated"))
        self._commit()
        return self.categories.get(category_id)

    def list_events(self, resource_type, resource_id, actor=None):
        self._authorize(actor, "audit")
        if resource_type not in {"payment", "expense", "expense_category"}:
            raise HTTPException(422, "Tipo de recurso financeiro invalido.")
        return self.events.list_for(resource_type, resource_id)

    def summary(self, start, end, regime="cash", actor=None,
                start_year=None, start_month=None, end_year=None, end_month=None):
        self._authorize(actor, "view")
        period_start, period_end, display_start, display_end = self._validate_period(
            start, end, regime, start_year, start_month, end_year, end_month
        )
        payments = self.payments.list_filtered(period_start, period_end, regime)
        expenses = self.expenses.list_filtered(period_start, period_end, regime, "active")
        if regime == "cash":
            income = sum(item.amount_cents for item in payments if item.status == "paid")
            receivable = 0
        else:
            income = sum(item.amount_cents for item in payments if item.status in {"pending", "paid"})
            receivable = sum(item.amount_cents for item in payments if item.status == "pending")
        expense_total = sum(item.amount_cents for item in expenses)
        return {
            "regime": regime,
            "start": display_start,
            "end": display_end,
            "income_cents": income,
            "receivable_cents": receivable,
            "expense_cents": expense_total,
            "balance_cents": income - expense_total,
        }
