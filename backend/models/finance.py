from enum import Enum

from sqlalchemy import CheckConstraint, Date, DateTime, DDL, ForeignKey, Index, Integer, String, Text, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"
    REVERSED = "reversed"


class ExpenseStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="ck_expense_categories_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="1")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="NO ACTION"), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_payments_amount_positive"),
        CheckConstraint("competence_year BETWEEN 1 AND 9999", name="ck_payments_competence_year"),
        CheckConstraint("competence_month BETWEEN 1 AND 12", name="ck_payments_competence_month"),
        CheckConstraint("status IN ('pending','paid','canceled','reversed')", name="ck_payments_status"),
        CheckConstraint(
            "(status = 'pending' AND paid_at IS NULL AND canceled_at IS NULL AND reversed_at IS NULL) OR "
            "(status = 'paid' AND paid_at IS NOT NULL AND canceled_at IS NULL AND reversed_at IS NULL) OR "
            "(status = 'canceled' AND paid_at IS NULL AND canceled_at IS NOT NULL AND reversed_at IS NULL AND length(trim(cancellation_reason)) > 0) OR "
            "(status = 'reversed' AND paid_at IS NOT NULL AND canceled_at IS NULL AND reversed_at IS NOT NULL AND length(trim(reversal_reason)) > 0)",
            name="ck_payments_lifecycle",
        ),
        Index("ix_payments_cash_period", "status", "paid_at"),
        Index("ix_payments_accrual_period", "competence_year", "competence_month", "status"),
        Index("ix_payments_due_status", "due_date", "status"),
        Index("ix_payments_patient", "patient_id"),
        Index("ix_payments_appointment", "appointment_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="NO ACTION"), nullable=False)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id", ondelete="NO ACTION"), nullable=True)
    competence_year: Mapped[int] = mapped_column(Integer, nullable=False)
    competence_month: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date = mapped_column(Date, nullable=False)
    paid_at = mapped_column(Date, nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=PaymentStatus.PENDING.value, server_default="pending")
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default="", server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="NO ACTION"), nullable=True)
    canceled_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="NO ACTION"), nullable=True)
    reversed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="NO ACTION"), nullable=True)
    canceled_at = mapped_column(DateTime(timezone=True), nullable=True)
    reversed_at = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    reversal_reason: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    patient = relationship("Patient")
    appointment = relationship("Appointment")


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_expenses_amount_positive"),
        CheckConstraint("competence_year BETWEEN 1 AND 9999", name="ck_expenses_competence_year"),
        CheckConstraint("competence_month BETWEEN 1 AND 12", name="ck_expenses_competence_month"),
        CheckConstraint("status IN ('active','canceled')", name="ck_expenses_status"),
        CheckConstraint(
            "(status = 'active' AND canceled_at IS NULL) OR "
            "(status = 'canceled' AND canceled_at IS NOT NULL AND length(trim(cancellation_reason)) > 0)",
            name="ck_expenses_lifecycle",
        ),
        Index("ix_expenses_cash_period", "expense_date", "status"),
        Index("ix_expenses_accrual_period", "competence_year", "competence_month", "status"),
        Index("ix_expenses_category", "category_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    expense_date = mapped_column(Date, nullable=False)
    competence_year: Mapped[int] = mapped_column(Integer, nullable=False)
    competence_month: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("expense_categories.id", ondelete="NO ACTION"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=ExpenseStatus.ACTIVE.value, server_default="active")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="NO ACTION"), nullable=True)
    canceled_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="NO ACTION"), nullable=True)
    canceled_at = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    category = relationship("ExpenseCategory")


class FinancialEvent(Base):
    __tablename__ = "financial_events"
    __table_args__ = (
        CheckConstraint("resource_type IN ('payment','expense','expense_category')", name="ck_financial_events_resource_type"),
        CheckConstraint("length(trim(event_type)) > 0", name="ck_financial_events_event_type"),
        Index("ix_financial_events_resource", "resource_type", "resource_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="NO ACTION"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LegacyFinancialQuarantine(Base):
    __tablename__ = "legacy_financial_quarantine"
    __table_args__ = (
        CheckConstraint("length(source_database_sha256)=64 AND length(source_record_sha256)=64"),
        CheckConstraint("length(source_manifest_sha256)=64 AND length(mapping_sha256)=64"),
        CheckConstraint("source_generation > 0"),
        CheckConstraint("source_entity_type IN ('payment','expense')"),
        CheckConstraint("source_record_id > 0"),
        CheckConstraint("reason_code = 'PAID_WITH_UNKNOWN_PAID_AT'"),
        CheckConstraint("decision_id = 'D005-10'"),
        CheckConstraint("resolution_state = 'unresolved'"),
        CheckConstraint("amount_cents > 0"),
        CheckConstraint("competence_year BETWEEN 1 AND 9999"),
        CheckConstraint("competence_month BETWEEN 1 AND 12"),
        Index("ux_legacy_quarantine_source", "source_database_sha256", "source_entity_type", "source_record_id", unique=True),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_database_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_generation: Mapped[int] = mapped_column(Integer, nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    source_record_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    legacy_status: Mapped[str] = mapped_column(String(30), nullable=False)
    legacy_amount_text: Mapped[str] = mapped_column(Text, nullable=False)
    legacy_currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="BRL")
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    competence_year: Mapped[int] = mapped_column(Integer, nullable=False)
    competence_month: Mapped[int] = mapped_column(Integer, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(40), nullable=False)
    quarantined_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    decision_id: Mapped[str] = mapped_column(String(20), nullable=False)
    source_manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    migration_execution_id: Mapped[str] = mapped_column(String(64), nullable=False)
    resolution_state: Mapped[str] = mapped_column(String(20), nullable=False, server_default="unresolved")
    legacy_row_json: Mapped[str] = mapped_column(Text, nullable=False)


class LegacyFinancialQuarantineEvent(Base):
    __tablename__ = "legacy_financial_quarantine_events"
    __table_args__ = (
        CheckConstraint("length(trim(actor))>0 AND length(trim(action))>0 AND length(evidence_sha256)=64"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quarantine_id: Mapped[int] = mapped_column(ForeignKey("legacy_financial_quarantine.id", ondelete="NO ACTION"), nullable=False)
    actor: Mapped[str] = mapped_column(String(40), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


for table in (Payment.__table__, Expense.__table__, ExpenseCategory.__table__):
    event.listen(table, "after_create", DDL(f"""
CREATE TRIGGER IF NOT EXISTS spec005_{table.name}_no_delete
BEFORE DELETE ON {table.name}
BEGIN SELECT RAISE(ABORT, '{table.name} history is protected'); END
"""))

event.listen(FinancialEvent.__table__, "after_create", DDL("""
CREATE TRIGGER IF NOT EXISTS spec005_financial_events_no_update
BEFORE UPDATE ON financial_events
BEGIN SELECT RAISE(ABORT, 'financial_events is append-only'); END
"""))
for table in (LegacyFinancialQuarantine.__table__, LegacyFinancialQuarantineEvent.__table__):
    for action in ("update", "delete"):
        event.listen(table, "after_create", DDL(f"""
CREATE TRIGGER IF NOT EXISTS spec005_{table.name}_no_{action}
BEFORE {action.upper()} ON {table.name}
BEGIN SELECT RAISE(ABORT, '{table.name} is append-only'); END
"""))
event.listen(FinancialEvent.__table__, "after_create", DDL("""
CREATE TRIGGER IF NOT EXISTS spec005_financial_events_no_delete
BEFORE DELETE ON financial_events
BEGIN SELECT RAISE(ABORT, 'financial_events is append-only'); END
"""))
