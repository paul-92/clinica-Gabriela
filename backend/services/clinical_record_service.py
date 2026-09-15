import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.models.appointment import Appointment
from backend.models.clinical_record import ClinicalRecordAuditEvent, ClinicalRecordRevision
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.repositories.clinical_record_repository import ClinicalRecordRepository
from backend.services.errors import translate_integrity_error


CONTENT_FIELDS = (
    "main_complaint", "session_goals", "observed_mood", "clinical_evolution",
    "interventions", "referrals", "next_steps", "private_notes",
    "clinical_hypotheses", "therapeutic_plan", "future_attachments",
)


class ClinicalRecordService:
    def __init__(self, db):
        self.db = db
        self.repository = ClinicalRecordRepository(db)

    def list_records(self, patient_id=None):
        if patient_id:
            if self.db.get(Patient, patient_id) is None:
                raise HTTPException(status_code=404, detail="Paciente nao encontrado.")
            return self.repository.by_patient(patient_id)
        return self.repository.list_all()

    def get_record(self, record_id):
        record = self.repository.get(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Prontuario nao encontrado.")
        return record

    def create_record(self, data, current_user):
        self._validate_relations(data, require_active=True)
        data.update(author_user_id=current_user.id, author_status="identified", status="draft")
        try:
            return self.repository.create(data)
        except IntegrityError as exc:
            translate_integrity_error(self.db, exc)

    def update_record(self, record_id, data, expected_version):
        record = self.get_record(record_id)
        self._check_version(record, expected_version)
        if record.status != "draft":
            raise HTTPException(status_code=409, detail="Somente prontuario em rascunho pode ser editado.")
        data["version"] = record.version + 1
        return self.repository.update(record, data)

    def finalize_record(self, record_id, expected_version, current_user):
        record = self.get_record(record_id)
        self._check_version(record, expected_version)
        if record.status != "draft":
            raise HTTPException(status_code=409, detail="Prontuario nao esta em rascunho.")
        if record.author_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Somente o autor pode finalizar o rascunho.")
        return self.repository.update(record, {
            "status": "finalized", "finalized_at": datetime.now(),
            "version": record.version + 1,
        })

    def rectify_record(self, record_id, data, current_user):
        record = self.get_record(record_id)
        if record.status not in {"finalized", "legacy_preserved"}:
            raise HTTPException(status_code=409, detail="Retificacao exige prontuario preservado ou finalizado.")
        reason = data.pop("reason", "").strip()
        if not reason:
            raise HTTPException(status_code=422, detail="Motivo da retificacao obrigatorio.")
        previous = self.repository.latest_revision(record.id)
        snapshot = {field: data.get(field, getattr(record, field) or "") for field in CONTENT_FIELDS}
        revision = ClinicalRecordRevision(
            clinical_record_id=record.id,
            previous_revision_id=previous.id if previous else None,
            author_user_id=current_user.id,
            psychologist_id=record.psychologist_id,
            reason=reason,
            content_snapshot=json.dumps(snapshot, ensure_ascii=False, sort_keys=True),
        )
        self.db.add(revision)
        try:
            self.db.commit()
            self.db.refresh(revision)
            return revision
        except IntegrityError as exc:
            translate_integrity_error(self.db, exc)

    def delete_draft(self, record_id, current_user):
        record = self.get_record(record_id)
        if record.status != "draft" or record.finalized_at is not None:
            raise HTTPException(status_code=409, detail="Prontuario preservado ou finalizado nao pode ser excluido.")
        if record.author_user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Usuario sem permissao para excluir o rascunho.")
        if self.repository.latest_revision(record.id) is not None:
            raise HTTPException(status_code=409, detail="Rascunho com dependencia deve ser preservado.")
        self.db.add(ClinicalRecordAuditEvent(
            record_reference=record.id, actor_user_id=current_user.id,
            event_type="draft_deleted",
        ))
        self.db.delete(record)
        try:
            self.db.commit()
        except IntegrityError as exc:
            translate_integrity_error(self.db, exc)

    def _validate_relations(self, data, require_active):
        patient = self.db.get(Patient, data["patient_id"])
        psychologist = self.db.get(Psychologist, data["psychologist_id"])
        if patient is None:
            raise HTTPException(status_code=404, detail="Paciente nao encontrado.")
        if psychologist is None:
            raise HTTPException(status_code=404, detail="Psicologo nao encontrado.")
        if require_active and not patient.active:
            raise HTTPException(status_code=409, detail="Paciente inativo para novo fato clinico.")
        if require_active and (not psychologist.active or psychologist.crp_status != "apt"):
            raise HTTPException(status_code=409, detail="Psicologo nao esta apto para atuacao clinica.")
        appointment_id = data.get("appointment_id")
        if appointment_id is not None:
            appointment = self.db.get(Appointment, appointment_id)
            if appointment is None:
                raise HTTPException(status_code=404, detail="Atendimento nao encontrado.")
            if appointment.patient_id != patient.id or appointment.psychologist_id != psychologist.id:
                raise HTTPException(status_code=409, detail="Atendimento incoerente com paciente ou psicologo.")

    @staticmethod
    def _check_version(record, expected):
        if expected is None:
            raise HTTPException(status_code=428, detail="If-Match obrigatorio.")
        if expected != record.version:
            raise HTTPException(status_code=412, detail="Versao do recurso desatualizada.")
