from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base


class Psychologist(Base):
    __tablename__ = "psychologists"
    __table_args__ = (UniqueConstraint("crp_region", "crp_number", name="uq_psychologist_crp_identity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    crp: Mapped[str | None] = mapped_column(String(40), nullable=True)
    crp_region: Mapped[str | None] = mapped_column(String(8), nullable=True)
    crp_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    crp_status: Mapped[str] = mapped_column(String(30), nullable=False, default="provisional", server_default="provisional")
    phone: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    specialty: Mapped[str] = mapped_column(String(120), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime, server_default=func.now())
    updated_at = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    appointments = relationship("Appointment", back_populates="psychologist")
    clinical_records = relationship("ClinicalRecord", back_populates="psychologist")
