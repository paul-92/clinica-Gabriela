import sqlite3
from pathlib import Path


def migrate_spec004(database: str | Path) -> dict:
    """Forward-only v4 migration. Must be run on an isolated candidate copy."""
    path = Path(database).resolve(strict=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=DELETE")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version >= 4:
            return {"user_version": version, "legacy_rescheduled": 0, "idempotent": True}
        legacy = connection.execute("SELECT COUNT(*) FROM appointments WHERE status='rescheduled'").fetchone()[0]
        connection.execute("BEGIN IMMEDIATE")
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
            if "psychologist_id" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN psychologist_id INTEGER REFERENCES psychologists(id) ON DELETE NO ACTION")
                connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_psychologist_id ON users(psychologist_id) WHERE psychologist_id IS NOT NULL")
            settings = {row[1] for row in connection.execute("PRAGMA table_info(clinic_settings)")}
            if "timezone_name" not in settings:
                connection.execute("ALTER TABLE clinic_settings ADD COLUMN timezone_name TEXT NOT NULL DEFAULT 'America/Sao_Paulo'")
            appointment_columns = {row[1] for row in connection.execute("PRAGMA table_info(appointments)")}
            for name, definition in (
                ("original_appointment_id", "INTEGER REFERENCES appointments(id) ON DELETE NO ACTION"),
                ("timezone_name", "TEXT NOT NULL DEFAULT 'America/Sao_Paulo'"),
                ("temporal_status", "TEXT NOT NULL DEFAULT 'legacy_unverified'"),
            ):
                if name not in appointment_columns:
                    connection.execute(f"ALTER TABLE appointments ADD COLUMN {name} {definition}")
            connection.execute("""CREATE TABLE IF NOT EXISTS appointment_events (
                id INTEGER PRIMARY KEY, appointment_id INTEGER NOT NULL REFERENCES appointments(id) ON DELETE NO ACTION,
                successor_appointment_id INTEGER REFERENCES appointments(id) ON DELETE NO ACTION,
                actor_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE NO ACTION,
                event_type TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            connection.execute("CREATE INDEX IF NOT EXISTS ix_appointments_psychologist_start_status ON appointments(psychologist_id,scheduled_at,status)")
            connection.execute("CREATE INDEX IF NOT EXISTS ix_appointment_events_appointment_created ON appointment_events(appointment_id,created_at)")
            connection.execute("""CREATE TRIGGER IF NOT EXISTS spec004_appointments_insert_guard BEFORE INSERT ON appointments
                WHEN NEW.duration_minutes <= 0 OR NEW.status NOT IN ('scheduled','done','canceled','no_show')
                BEGIN SELECT RAISE(ABORT, 'invalid appointment domain'); END""")
            connection.execute("""CREATE TRIGGER IF NOT EXISTS spec004_appointments_update_guard BEFORE UPDATE OF duration_minutes,status ON appointments
                WHEN NEW.duration_minutes <= 0 OR NEW.status NOT IN ('scheduled','done','canceled','no_show')
                BEGIN SELECT RAISE(ABORT, 'invalid appointment domain'); END""")
            connection.execute("PRAGMA user_version=4")
            connection.commit()
        except Exception:
            connection.rollback(); raise
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or list(connection.execute("PRAGMA foreign_key_check")):
            raise RuntimeError("Candidato SPEC-004 falhou na integridade")
        return {"user_version": 4, "legacy_rescheduled": legacy, "legacy_policy": "preserved_unverified"}
