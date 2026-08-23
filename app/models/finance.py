from enum import Enum

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class PaymentStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    CANCELED = "canceled"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    appointment_id = mapped_column(ForeignKey("appointments.id"), nullable=True)
    due_date = mapped_column(Date, nullable=False)
    paid_at = mapped_column(Date, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=PaymentStatus.PENDING.value)
    payment_method: Mapped[str] = mapped_column(String(50), default="")
    description = mapped_column(Text, default="")

    patient = relationship("Patient")
    appointment = relationship("Appointment")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    expense_date = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="")
