import sqlite3
from pathlib import Path


def migrate_spec004_remediation(database: str | Path) -> dict:
    """Forward-only SPEC-004 remediation migration from schema v4 to v5."""
    path = Path(database).resolve(strict=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=DELETE")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version >= 5:
            return {"user_version": version, "idempotent": True}
        if version != 4:
            raise RuntimeError("migration corretiva exige user_version=4")
        duplicates = list(connection.execute(
            "SELECT original_appointment_id, COUNT(*) FROM appointments "
            "WHERE original_appointment_id IS NOT NULL GROUP BY original_appointment_id HAVING COUNT(*) > 1"
        ))
        if duplicates:
            raise RuntimeError("sucessores multiplos exigem decisao; migration abortada")
        connection.execute("BEGIN IMMEDIATE")
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(appointment_events)")}
            if "from_status" not in columns:
                connection.execute("ALTER TABLE appointment_events ADD COLUMN from_status TEXT")
            if "to_status" not in columns:
                connection.execute("ALTER TABLE appointment_events ADD COLUMN to_status TEXT")
            connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_appointments_original_successor ON appointments(original_appointment_id) WHERE original_appointment_id IS NOT NULL")
            connection.execute("""CREATE TRIGGER IF NOT EXISTS spec004_events_no_update BEFORE UPDATE ON appointment_events
                BEGIN SELECT RAISE(ABORT, 'appointment_events is append-only'); END""")
            connection.execute("""CREATE TRIGGER IF NOT EXISTS spec004_events_no_delete BEFORE DELETE ON appointment_events
                BEGIN SELECT RAISE(ABORT, 'appointment_events is append-only'); END""")
            connection.execute("""CREATE TRIGGER IF NOT EXISTS spec004_reschedule_event_guard BEFORE INSERT ON appointment_events
                WHEN NEW.event_type='rescheduled' AND (NEW.successor_appointment_id IS NULL OR NOT EXISTS
                (SELECT 1 FROM appointments s WHERE s.id=NEW.successor_appointment_id AND s.original_appointment_id=NEW.appointment_id))
                BEGIN SELECT RAISE(ABORT, 'invalid reschedule relationship'); END""")
            connection.execute("PRAGMA user_version=5")
            connection.commit()
        except Exception:
            connection.rollback(); raise
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        fk = list(connection.execute("PRAGMA foreign_key_check"))
        if integrity != "ok" or fk:
            raise RuntimeError("candidato v5 falhou na integridade")
        return {"user_version": 5, "integrity_check": integrity,
                "foreign_key_violations": len(fk), "idempotent": False}
