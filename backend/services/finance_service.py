from backend.repositories.finance_repository import ExpenseRepository, PaymentRepository
from backend.models.appointment import Appointment
from backend.models.patient import Patient
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from backend.services.errors import translate_integrity_error


class FinanceService:
    def __init__(self, db):
        self.payments = PaymentRepository(db)
        self.expenses = ExpenseRepository(db)

    def list_payments(self):
        return self.payments.list_recent()

    def create_payment(self, data):
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
        try:
            return self.payments.create(data)
        except IntegrityError as exc:
            translate_integrity_error(self.payments.db, exc)

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
