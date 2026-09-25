from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.session import Base
from backend.models.clinical_record import ClinicalRecord
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.user import User
from backend.services.clinical_record_service import ClinicalRecordService


def build_session():
    from backend.models import appointment, clinical_record, finance, patient, psychologist, settings, user  # noqa: F401

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def add_fixture(session):
    patient = Patient(full_name="Paciente Ficticio", active=True)
    first_psychologist = Psychologist(full_name="Psicologo Um", crp_status="apt", active=True)
    second_psychologist = Psychologist(full_name="Psicologo Dois", crp_status="apt", active=True)
    session.add_all([patient, first_psychologist, second_psychologist])
    session.flush()
    first_user = User(name="Psi Um", username="psi-um", password_hash="disabled", role="psychologist", active=True, psychologist_id=first_psychologist.id)
    second_user = User(name="Psi Dois", username="psi-dois", password_hash="disabled", role="psychologist", active=True, psychologist_id=second_psychologist.id)
    session.add_all([first_user, second_user])
    session.commit()
    return patient, first_psychologist, second_psychologist, first_user, second_user


def record_payload(patient_id, psychologist_id):
    return {
        "patient_id": patient_id,
        "psychologist_id": psychologist_id,
        "appointment_date": datetime(2030, 1, 1, 10),
        "clinical_evolution": "conteudo clinico sintetico",
    }


def test_clinical_records_are_scoped_to_linked_psychologist():
    session = build_session()
    try:
        patient, first_psychologist, second_psychologist, first_user, second_user = add_fixture(session)
        service = ClinicalRecordService(session)
        first_record = service.create_record(record_payload(patient.id, first_psychologist.id), first_user)
        second_record = service.create_record(record_payload(patient.id, second_psychologist.id), second_user)

        assert service.list_records(current_user=first_user) == [first_record]
        assert service.get_record(first_record.id, first_user).id == first_record.id
        with pytest.raises(Exception) as denied_read:
            service.get_record(second_record.id, first_user)
        assert denied_read.value.status_code == 404
        with pytest.raises(Exception) as denied_update:
            service.update_record(second_record.id, {"clinical_evolution": "tentativa"}, second_record.version, first_user)
        assert denied_update.value.status_code == 404
        with pytest.raises(Exception) as denied_create:
            service.create_record(record_payload(patient.id, second_psychologist.id), first_user)
        assert denied_create.value.status_code == 403
    finally:
        session.close()


def test_unlinked_psychologist_fails_closed():
    session = build_session()
    try:
        _, _, _, _, _ = add_fixture(session)
        unlinked = User(name="Psi Sem Vinculo", username="psi-sem-vinculo", password_hash="disabled", role="psychologist", active=True)
        session.add(unlinked)
        session.commit()
        with pytest.raises(Exception) as denied:
            ClinicalRecordService(session).list_records(current_user=unlinked)
        assert denied.value.status_code == 403
    finally:
        session.close()
