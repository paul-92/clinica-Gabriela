from sqlalchemy import inspect, text

from app.database.session import engine


CLINICAL_RECORD_COLUMNS = {
    "main_complaint": "TEXT DEFAULT ''",
    "session_goals": "TEXT DEFAULT ''",
    "observed_mood": "TEXT DEFAULT ''",
    "interventions": "TEXT DEFAULT ''",
    "referrals": "TEXT DEFAULT ''",
    "next_steps": "TEXT DEFAULT ''",
}


def run_light_migrations():
    inspector = inspect(engine)
    if "clinical_records" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("clinical_records")}
    with engine.begin() as connection:
        for column, definition in CLINICAL_RECORD_COLUMNS.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE clinical_records ADD COLUMN {column} {definition}"))
