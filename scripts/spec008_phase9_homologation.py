"""Homologação isolada da Fase 9 da SPEC-008, sem cutover."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path


DISABLED_CREDENTIAL = "!DISABLED_CREDENTIAL:v1!"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect(response, status: int, label: str):
    if response.status_code != status:
        raise RuntimeError(f"{label}: HTTP {response.status_code}")
    return response.json()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def run(database: Path, backup: Path, restore: Path) -> dict:
    database = database.resolve(strict=True)
    initial_checksum = _sha256(database)

    # Imports tardios: BACKEND_DATABASE_PATH deve ser configurado pelo executor.
    from fastapi.testclient import TestClient

    import backend.main as backend_main
    from backend.database.session import create_database_runtime
    from backend.models.user import User
    from backend.config import RuntimeSettings
    from backend.utils.security import hash_password

    backend_main.license_status = lambda: {"valid": True}
    settings = RuntimeSettings(database.parent, database, "127.0.0.1", 8765, False)
    runtime = create_database_runtime(settings)
    synthetic_password = "Spec008-Homologation-Only!"
    try:
        with runtime.session_factory() as session:
            users = session.query(User).order_by(User.id).all()
            if not users or any(
                not user.password_reset_required or user.password_hash != DISABLED_CREDENTIAL
                for user in users
            ):
                raise RuntimeError("estado migrado de credenciais diverge da politica")
            admin = next((user for user in users if user.role == "admin"), None)
            psychologist = next((user for user in users if user.role == "psychologist"), None)
            disabled = next((user for user in users if user not in {admin, psychologist}), None)
            if not admin or not psychologist or not disabled:
                raise RuntimeError("papeis minimos para homologacao ausentes")

            # Hash válido + reset obrigatório ainda deve bloquear autenticação.
            admin.password_hash = hash_password(synthetic_password)
            session.commit()
            reset_username = admin.username
            disabled_username = disabled.username

        app = backend_main.create_app()
        with TestClient(app) as client:
            _expect(client.get("/health"), 200, "health")
            _expect(
                client.post("/auth/login", json={"username": reset_username, "password": synthetic_password}),
                401,
                "password_reset_required",
            )

            with runtime.session_factory() as session:
                admin = session.query(User).filter(User.username == reset_username).one()
                admin.password_reset_required = False
                psychologist = session.query(User).filter(User.role == "psychologist").one()
                psychologist.password_hash = hash_password(synthetic_password)
                psychologist.password_reset_required = False
                disabled = session.query(User).filter(User.username == disabled_username).one()
                disabled.password_reset_required = False
                session.commit()

            _expect(
                client.post("/auth/login", json={"username": disabled_username, "password": synthetic_password}),
                401,
                "disabled_credential",
            )
            admin_login = _expect(
                client.post("/auth/login", json={"username": reset_username, "password": synthetic_password}),
                200,
                "admin_login",
            )
            with runtime.session_factory() as session:
                psychologist_username = session.query(User).filter(User.role == "psychologist").one().username
            psychologist_login = _expect(
                client.post("/auth/login", json={"username": psychologist_username, "password": synthetic_password}),
                200,
                "psychologist_login",
            )
            admin_headers = _headers(admin_login["access_token"])
            psychologist_headers = _headers(psychologist_login["access_token"])

            patient = _expect(client.post("/patients", headers=admin_headers, json={
                "full_name": "Paciente Homologacao", "cpf": "000.000.000-00",
                "birth_date": "1990-01-01", "notes": "dado sintetico",
            }), 201, "patients.create")
            _expect(client.get(f"/patients/{patient['id']}", headers=admin_headers), 200, "patients.get")
            _expect(client.put(f"/patients/{patient['id']}", headers=admin_headers,
                               json={"phone": "(00) 00000-0000"}), 200, "patients.update")

            psychologist_row = _expect(client.post("/psychologists", headers=admin_headers, json={
                "full_name": "Psicologo Homologacao", "crp": "00/00000",
                "specialty": "Homologacao",
            }), 201, "psychologists.create")
            _expect(client.get(f"/psychologists/{psychologist_row['id']}", headers=admin_headers),
                    200, "psychologists.get")

            appointment_payload = {
                "patient_id": patient["id"], "psychologist_id": psychologist_row["id"],
                "scheduled_at": "2030-01-15T10:00:00", "duration_minutes": 50,
                "status": "scheduled", "notes": "homologacao",
            }
            appointment = _expect(client.post("/appointments", headers=admin_headers,
                                               json=appointment_payload), 201, "appointments.create")
            _expect(client.get(f"/appointments/{appointment['id']}", headers=admin_headers),
                    200, "appointments.get")
            _expect(client.post("/appointments", headers=admin_headers, json=appointment_payload),
                    409, "appointments.conflict")

            clinical = _expect(client.post("/clinical-records", headers=psychologist_headers, json={
                "patient_id": patient["id"], "psychologist_id": psychologist_row["id"],
                "appointment_date": "2030-01-15T10:00:00", "main_complaint": "sintetico",
            }), 201, "clinical_records.create")
            _expect(client.get(f"/clinical-records/{clinical['id']}", headers=psychologist_headers),
                    200, "clinical_records.get")
            _expect(client.get("/clinical-records", headers=admin_headers), 403,
                    "clinical_records.access")

            _expect(client.post("/finance/payments", headers=admin_headers, json={
                "patient_id": patient["id"], "appointment_id": appointment["id"],
                "due_date": "2030-01-15", "paid_at": "2030-01-15", "amount": 123.45,
                "status": "paid", "payment_method": "teste", "description": "homologacao",
            }), 201, "payments.create")
            _expect(client.post("/finance/expenses", headers=admin_headers, json={
                "description": "Despesa homologacao", "amount": 23.45,
                "expense_date": "2030-01-15", "category": "teste",
            }), 201, "expenses.create")
            _expect(client.get("/finance/summary", headers=admin_headers), 200, "finance.summary")

            settings_payload = {
                "clinic_name": "Clinica Homologacao", "phone": "", "email": "",
                "address": "", "default_session_value": 200.0,
            }
            _expect(client.put("/settings", headers=admin_headers, json=settings_payload),
                    200, "clinic_settings.update")
            _expect(client.get("/settings", headers=admin_headers), 200, "clinic_settings.get")

        # Novo lifespan comprova persistência após reinício lógico do backend.
        with TestClient(backend_main.create_app()) as client:
            login = _expect(client.post("/auth/login", json={
                "username": reset_username, "password": synthetic_password,
            }), 200, "restart.login")
            headers = _headers(login["access_token"])
            _expect(client.get(f"/patients/{patient['id']}", headers=headers), 200,
                    "restart.patient_persisted")
            _expect(client.get(f"/appointments/{appointment['id']}", headers=headers), 200,
                    "restart.appointment_persisted")

        runtime.engine.dispose()
        with sqlite3.connect(database) as source, sqlite3.connect(backup) as target:
            source.backup(target)
        shutil.copyfile(backup, restore)
        with sqlite3.connect(f"file:{restore.as_posix()}?mode=ro&immutable=1", uri=True) as restored:
            integrity = [row[0] for row in restored.execute("PRAGMA integrity_check")]
            fk_violations = sum(1 for _ in restored.execute("PRAGMA foreign_key_check"))
            persisted = restored.execute(
                "SELECT COUNT(*) FROM patients WHERE id=?", (patient["id"],)
            ).fetchone()[0]
        if integrity != ["ok"] or fk_violations or persisted != 1:
            raise RuntimeError("backup/restauracao nao preservou integridade e persistencia")

        return {
            "gate": "PASS",
            "candidate_initial_checksum_sha256": initial_checksum,
            "flows": {
                "health": "PASS", "authentication": "PASS",
                "password_reset_required": "PASS", "disabled_credential": "PASS",
                "patients": "PASS", "psychologists": "PASS", "appointments": "PASS",
                "clinical_records": "PASS", "payments": "PASS", "expenses": "PASS",
                "clinic_settings": "PASS", "persistence_after_restart": "PASS",
                "backup_restore": "PASS",
            },
            "restore_integrity_check": "ok",
            "restore_foreign_key_violations": 0,
            "privacy_safe": True,
            "cutover_authorized": False,
        }
    finally:
        runtime.engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument("--restore", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.database, args.backup, args.restore), sort_keys=True))


if __name__ == "__main__":
    main()
