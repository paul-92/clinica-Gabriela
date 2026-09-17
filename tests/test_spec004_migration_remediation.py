import shutil
import sqlite3

import pytest

from backend.migration.spec004_remediation import migrate_spec004_remediation
from backend.migration.spec004 import migrate_spec004


def test_v4_to_v5_preserves_content_and_materializes_guards(tmp_path):
    source = tmp_path / "v4.db"
    with sqlite3.connect(source) as db:
        db.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE appointments(id INTEGER PRIMARY KEY, original_appointment_id INTEGER REFERENCES appointments(id));
        CREATE TABLE users(id INTEGER PRIMARY KEY);
        CREATE TABLE appointment_events(id INTEGER PRIMARY KEY, appointment_id INTEGER NOT NULL REFERENCES appointments(id), successor_appointment_id INTEGER REFERENCES appointments(id), actor_user_id INTEGER NOT NULL REFERENCES users(id), event_type TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP);
        INSERT INTO users VALUES(7);
        INSERT INTO appointments VALUES(11,NULL);
        INSERT INTO appointments VALUES(29,11);
        INSERT INTO appointment_events(id,appointment_id,successor_appointment_id,actor_user_id,event_type,reason,created_at) VALUES(41,11,29,7,'rescheduled','canario','2020-01-02 03:04:05');
        PRAGMA user_version=4;
        """)
    before = source.read_bytes()
    result = migrate_spec004_remediation(source)
    assert result["user_version"] == 5
    with sqlite3.connect(source) as db:
        assert db.execute("SELECT id,reason,created_at FROM appointment_events").fetchall() == [(41, "canario", "2020-01-02 03:04:05")]
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert list(db.execute("PRAGMA foreign_key_check")) == []
        assert "ux_appointments_original_successor" in {r[1] for r in db.execute("PRAGMA index_list(appointments)")}
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO appointments VALUES(30,11)")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE appointment_events SET reason='x' WHERE id=41")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM appointment_events WHERE id=41")
    assert migrate_spec004_remediation(source)["idempotent"] is True
    assert before != source.read_bytes()


def test_v5_aborts_on_preexisting_multiple_successors(tmp_path):
    database = tmp_path / "duplicates.db"
    with sqlite3.connect(database) as db:
        db.executescript("""
        CREATE TABLE appointments(id INTEGER PRIMARY KEY, original_appointment_id INTEGER REFERENCES appointments(id));
        CREATE TABLE appointment_events(id INTEGER PRIMARY KEY);
        INSERT INTO appointments VALUES(1,NULL); INSERT INTO appointments VALUES(2,1); INSERT INTO appointments VALUES(3,1);
        PRAGMA user_version=4;
        """)
    original = database.read_bytes()
    with pytest.raises(RuntimeError, match="sucessores multiplos"):
        migrate_spec004_remediation(database)
    assert database.read_bytes() == original


def test_v3_to_v4_to_v5_preserves_legacy_ids_timestamps_and_classification(tmp_path):
    database = tmp_path / "legacy-v3.db"
    with sqlite3.connect(database) as db:
        db.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE psychologists(id INTEGER PRIMARY KEY);
        CREATE TABLE patients(id INTEGER PRIMARY KEY);
        CREATE TABLE users(id INTEGER PRIMARY KEY);
        CREATE TABLE clinic_settings(id INTEGER PRIMARY KEY);
        CREATE TABLE appointments(id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id), psychologist_id INTEGER NOT NULL REFERENCES psychologists(id), scheduled_at DATETIME NOT NULL, duration_minutes INTEGER NOT NULL, status TEXT NOT NULL, notes TEXT, updated_at DATETIME, version INTEGER NOT NULL DEFAULT 1);
        INSERT INTO patients VALUES(13); INSERT INTO psychologists VALUES(17); INSERT INTO users VALUES(19); INSERT INTO clinic_settings VALUES(23);
        INSERT INTO appointments(id,patient_id,psychologist_id,scheduled_at,duration_minutes,status,notes,updated_at,version) VALUES(101,13,17,'2021-02-03 04:05:06',50,'rescheduled','canario legado','2021-02-03 05:06:07',4);
        PRAGMA user_version=3;
        """)
    assert migrate_spec004(database)["legacy_rescheduled"] == 1
    with sqlite3.connect(database) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 4
        assert db.execute("SELECT id,scheduled_at,status,notes,updated_at,version,temporal_status FROM appointments").fetchone() == (101, "2021-02-03 04:05:06", "rescheduled", "canario legado", "2021-02-03 05:06:07", 4, "legacy_unverified")
    assert migrate_spec004_remediation(database)["user_version"] == 5
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] == 1
        assert db.execute("SELECT id,scheduled_at,status,temporal_status FROM appointments").fetchone() == (101, "2021-02-03 04:05:06", "rescheduled", "legacy_unverified")
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert list(db.execute("PRAGMA foreign_key_check")) == []
