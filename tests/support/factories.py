"""Factories sintéticas, sem acesso a banco ou runtime operacional."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticUser:
    username: str = "user.synthetic"
    role: str = "reception"
    active: bool = True


@dataclass(frozen=True)
class SyntheticPatient:
    name: str = "Paciente Sintético"
    email: str = "paciente.synthetic@example.invalid"


@dataclass(frozen=True)
class SyntheticAppointment:
    patient_id: int = 1
    duration_minutes: int = 50
    status: str = "scheduled"


def make_synthetic_user(**overrides) -> SyntheticUser:
    return SyntheticUser(**overrides)


def make_synthetic_patient(**overrides) -> SyntheticPatient:
    return SyntheticPatient(**overrides)


def make_synthetic_appointment(**overrides) -> SyntheticAppointment:
    return SyntheticAppointment(**overrides)
