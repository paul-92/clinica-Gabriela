from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend.services.appointment_service import AppointmentService


class Existing:
    id = 1
    psychologist_id = 7
    scheduled_at = datetime(2030, 1, 15, 10, 0)
    duration_minutes = 50
    status = "scheduled"


class Repository:
    def __init__(self):
        self.existing = Existing()

    def active_for_psychologist(self, psychologist_id, *, exclude_id=None):
        if psychologist_id == 7 and exclude_id != self.existing.id:
            return [self.existing]
        return []

    def create(self, data):
        return data

    def get(self, appointment_id):
        return self.existing if appointment_id == self.existing.id else None

    def update(self, appointment, data):
        return appointment


def service():
    instance = AppointmentService.__new__(AppointmentService)
    instance.repository = Repository()
    return instance


@pytest.mark.parametrize("start", [
    datetime(2030, 1, 15, 9, 30),
    datetime(2030, 1, 15, 10, 0),
    datetime(2030, 1, 15, 10, 30),
])
def test_create_rejects_overlapping_appointment(start):
    with pytest.raises(HTTPException) as exc:
        service().create_appointment({
            "patient_id": 2, "psychologist_id": 7, "scheduled_at": start,
            "duration_minutes": 50, "status": "scheduled",
        })
    assert exc.value.status_code == 409


def test_create_allows_touching_boundary_and_canceled():
    active = service().create_appointment({
        "patient_id": 2, "psychologist_id": 7,
        "scheduled_at": Existing.scheduled_at + timedelta(minutes=50),
        "duration_minutes": 50, "status": "scheduled",
    })
    canceled = service().create_appointment({
        "patient_id": 2, "psychologist_id": 7,
        "scheduled_at": Existing.scheduled_at,
        "duration_minutes": 50, "status": "canceled",
    })
    assert active["status"] == "scheduled"
    assert canceled["status"] == "canceled"


def test_update_excludes_itself_from_conflict_check():
    assert service().update_appointment(1, {"duration_minutes": 60}) is not None
