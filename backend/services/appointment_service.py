from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.models.appointment import Appointment, AppointmentEvent
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.settings import ClinicSettings
from backend.repositories.appointment_repository import AppointmentRepository
from backend.services.errors import translate_integrity_error

OCCUPYING = {"scheduled", "done", "no_show"}
CLOSED = {"done", "canceled", "no_show"}


class AppointmentService:
    def __init__(self, db):
        self.repository = AppointmentRepository(db)
        self.db = db

    def list_appointments(self, target_date=None, psychologist_id=None, actor=None):
        if actor is not None and actor.role == "psychologist":
            if actor.psychologist_id is None:
                raise HTTPException(403, "Vinculo profissional obrigatorio.")
            psychologist_id = actor.psychologist_id
        return self.repository.list_filtered(target_date, psychologist_id)

    def get_appointment(self, appointment_id, actor=None):
        item = self.repository.get(appointment_id)
        if not item:
            raise HTTPException(404, "Atendimento nao encontrado.")
        if actor is not None:
            self._authorize(actor, item.psychologist_id, "view")
        return item

    def create_appointment(self, data, actor=None):
        if not hasattr(self, "db"):
            self._validate_availability(data)
            return self.repository.create(data)
        actor = self._require_actor(actor)
        self._begin_immediate()
        try:
            clean = dict(data)
            clean.setdefault("duration_minutes", 50)
            clean.setdefault("status", "scheduled")
            self._normalize_new_time(clean)
            self._authorize(actor, clean["psychologist_id"], "create")
            self._validate_relations(clean); self._validate_new(clean); self._validate_availability(clean)
            item = Appointment(**clean); self.db.add(item); self.db.flush()
            self._event(item.id, actor.id, "created")
            self.db.commit(); self.db.refresh(item)
            return item
        except HTTPException:
            self.db.rollback(); raise
        except IntegrityError as exc:
            translate_integrity_error(self.db, exc)
        except OperationalError:
            self.db.rollback(); raise HTTPException(409, "Agenda ocupada; tente novamente.")

    def update_appointment(self, appointment_id, data, actor=None, expected_version=None):
        if not hasattr(self, "db"):
            item = self.get_appointment(appointment_id)
            merged = {"psychologist_id": data.get("psychologist_id", item.psychologist_id),
                "scheduled_at": data.get("scheduled_at", item.scheduled_at),
                "duration_minutes": data.get("duration_minutes", item.duration_minutes),
                "status": data.get("status", item.status)}
            self._validate_availability(merged, exclude_id=item.id)
            return self.repository.update(item, data)
        actor = self._require_actor(actor); self._begin_immediate()
        try:
            item = self.get_appointment(appointment_id); self._precondition(item, expected_version)
            self._authorize(actor, item.psychologist_id, "edit")
            if item.status in CLOSED: raise HTTPException(409, "Atendimento encerrado nao pode ser editado.")
            if "status" in data and data["status"] != item.status: raise HTTPException(409, "Use a acao explicita de transicao.")
            merged = {"patient_id": data.get("patient_id", item.patient_id),
                "psychologist_id": data.get("psychologist_id", item.psychologist_id),
                "scheduled_at": data.get("scheduled_at", item.scheduled_at),
                "duration_minutes": data.get("duration_minutes", item.duration_minutes),
                "status": item.status, "timezone_name": data.get("timezone_name", item.timezone_name)}
            self._authorize(actor, merged["psychologist_id"], "edit")
            if "scheduled_at" in data:
                self._normalize_new_time(merged)
                data["scheduled_at"] = merged["scheduled_at"]
                data["timezone_name"] = merged["timezone_name"]
            self._validate_relations(merged); self._validate_new(merged, validate_time="scheduled_at" in data)
            self._validate_availability(merged, exclude_id=item.id)
            for key, value in data.items(): setattr(item, key, value)
            item.version += 1; self._event(item.id, actor.id, "updated")
            self.db.commit(); self.db.refresh(item); return item
        except Exception:
            self.db.rollback(); raise

    def transition(self, appointment_id, target, actor, expected_version, reason=""):
        self._begin_immediate()
        try:
            item = self.get_appointment(appointment_id); self._precondition(item, expected_version)
            if item.status != "scheduled" or target not in CLOSED: raise HTTPException(409, "Transicao de atendimento invalida.")
            self._authorize(actor, item.psychologist_id, target)
            item.status = target; item.version += 1; self._event(item.id, actor.id, target, reason=reason)
            self.db.commit(); self.db.refresh(item); return item
        except Exception:
            self.db.rollback(); raise

    def reschedule(self, appointment_id, data, actor, expected_version, reason):
        if not reason or not reason.strip(): raise HTTPException(422, "Motivo da remarcacao obrigatorio.")
        self._begin_immediate()
        try:
            original = self.get_appointment(appointment_id); self._precondition(original, expected_version)
            if original.status != "scheduled": raise HTTPException(409, "Somente atendimento agendado pode ser remarcado.")
            clean = dict(data); clean["status"] = "scheduled"; clean.setdefault("duration_minutes", 50)
            clean["original_appointment_id"] = original.id
            self._normalize_new_time(clean)
            self._authorize(actor, original.psychologist_id, "reschedule"); self._authorize(actor, clean["psychologist_id"], "reschedule")
            self._validate_relations(clean); self._validate_new(clean); self._validate_availability(clean, exclude_id=original.id)
            successor = Appointment(**clean); self.db.add(successor); self.db.flush()
            original.status = "canceled"; original.version += 1
            self._event(original.id, actor.id, "rescheduled", successor.id, reason.strip())
            self.db.commit(); self.db.refresh(successor); return successor
        except Exception:
            self.db.rollback(); raise

    def exceptional_correction(self, appointment_id, target, actor, expected_version, reason):
        if actor is None or actor.role != "admin":
            raise HTTPException(403, "Correcao excepcional exclusiva de administrador.")
        if not reason or not reason.strip():
            raise HTTPException(422, "Motivo da correcao excepcional obrigatorio.")
        if target not in {"scheduled", "done", "canceled", "no_show"}:
            raise HTTPException(422, "Estado de correcao invalido.")
        self._begin_immediate()
        try:
            item = self.get_appointment(appointment_id)
            self._precondition(item, expected_version)
            if item.status not in CLOSED or item.status == target:
                raise HTTPException(409, "Correcao excepcional exige estado encerrado e alteracao real.")
            previous = item.status
            item.status = target
            item.version += 1
            self._event(item.id, actor.id, "exceptional_correction", reason=reason.strip(),
                        from_status=previous, to_status=target)
            self.db.commit(); self.db.refresh(item); return item
        except Exception:
            self.db.rollback(); raise

    def _begin_immediate(self):
        try:
            self.db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        except OperationalError as exc:
            if "within a transaction" not in str(exc).lower(): raise HTTPException(409, "Agenda temporariamente indisponivel.") from exc

    @staticmethod
    def _require_actor(actor):
        if actor is None: raise HTTPException(403, "Ator autenticado obrigatorio.")
        return actor

    @staticmethod
    def _precondition(item, expected):
        if expected is None: raise HTTPException(428, "If-Match obrigatorio.")
        if expected != item.version: raise HTTPException(412, "Versao do recurso desatualizada.")

    @staticmethod
    def _authorize(actor, psychologist_id, action):
        if actor.role == "admin": return
        if actor.role == "reception":
            if action == "done": raise HTTPException(403, "Recepcao nao pode concluir atendimento.")
            return
        if actor.role == "psychologist" and actor.psychologist_id is not None and actor.psychologist_id == psychologist_id: return
        raise HTTPException(403, "Operacao fora do escopo autorizado.")

    def _validate_relations(self, data):
        patient = self.db.get(Patient, data["patient_id"]); psychologist = self.db.get(Psychologist, data["psychologist_id"])
        if patient is None: raise HTTPException(404, "Paciente nao encontrado.")
        if psychologist is None: raise HTTPException(404, "Psicologo nao encontrado.")
        if not patient.active: raise HTTPException(409, "Paciente inativo para novos atendimentos.")
        if not psychologist.active or psychologist.crp_status != "apt": raise HTTPException(409, "Psicologo nao esta apto.")

    @staticmethod
    def _validate_new(data, validate_time=True):
        if data.get("status") != "scheduled": raise HTTPException(422, "Status inicial invalido.")
        duration = data.get("duration_minutes", 50)
        if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0: raise HTTPException(422, "Duracao deve ser inteira e positiva.")
        if validate_time:
            instant = data["scheduled_at"]
            aware = instant.replace(tzinfo=timezone.utc) if instant.tzinfo is None else instant.astimezone(timezone.utc)
            if aware < datetime.now(timezone.utc): raise HTTPException(409, "Agendamento retroativo nao autorizado.")

    def _normalize_new_time(self, data):
        settings = self.db.query(ClinicSettings).order_by(ClinicSettings.id).limit(2).all()
        if len(settings) != 1:
            raise HTTPException(422, "Timezone efetivo da clinica nao configurado de forma unica.")
        name = settings[0].timezone_name
        try:
            zone = ZoneInfo(name)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(422, "Timezone efetivo da clinica invalido.") from exc
        supplied = data.get("timezone_name")
        if supplied and supplied != name:
            raise HTTPException(422, "Timezone do payload diverge da configuracao da clinica.")
        instant = data["scheduled_at"]
        if instant.tzinfo is None:
            valid = []
            for fold in (0, 1):
                candidate = instant.replace(tzinfo=zone, fold=fold)
                roundtrip = candidate.astimezone(timezone.utc).astimezone(zone)
                if roundtrip.replace(tzinfo=None) == instant and roundtrip.fold == fold:
                    valid.append(candidate)
            offsets = {candidate.utcoffset() for candidate in valid}
            if not valid:
                raise HTTPException(422, "Horario local inexistente por transicao DST.")
            if len(offsets) > 1:
                raise HTTPException(422, "Horario local ambiguo por transicao DST.")
            aware = valid[0]
        else:
            aware = instant.astimezone(zone)
        data["scheduled_at"] = aware.astimezone(timezone.utc).replace(tzinfo=None)
        data["timezone_name"] = name

    def _validate_availability(self, data, exclude_id=None):
        if data.get("status") == "canceled":
            return
        start = self._db_instant(data["scheduled_at"]); end = start + timedelta(minutes=data.get("duration_minutes", 50))
        for existing in self.repository.active_for_psychologist(data["psychologist_id"], exclude_id=exclude_id):
            if existing.status not in OCCUPYING: continue
            existing_start = self._db_instant(existing.scheduled_at)
            if start < existing_start + timedelta(minutes=existing.duration_minutes) and existing_start < end:
                raise HTTPException(409, "Conflito de horario para o psicologo.")

    @staticmethod
    def _db_instant(value):
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

    def _event(self, appointment_id, actor_id, event_type, successor_id=None, reason="",
               from_status=None, to_status=None):
        self.db.add(AppointmentEvent(appointment_id=appointment_id, successor_appointment_id=successor_id,
            actor_user_id=actor_id, event_type=event_type, reason=reason,
            from_status=from_status, to_status=to_status))
