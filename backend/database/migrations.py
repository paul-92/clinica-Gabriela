from sqlalchemy import inspect, text

from backend.database.session import engine


CLINICAL_RECORD_COLUMNS = {
    "main_complaint": "TEXT DEFAULT ''",
    "session_goals": "TEXT DEFAULT ''",
    "observed_mood": "TEXT DEFAULT ''",
    "interventions": "TEXT DEFAULT ''",
    "referrals": "TEXT DEFAULT ''",
    "next_steps": "TEXT DEFAULT ''",
}

USER_COLUMNS = {
    "password_reset_required": "BOOLEAN NOT NULL DEFAULT 0",
}


def run_light_migrations(bind=None):
    target_engine = bind or engine
    inspector = inspect(target_engine)
    tables = set(inspector.get_table_names())
    with target_engine.begin() as connection:
        for table, definitions in (
            ("clinical_records", CLINICAL_RECORD_COLUMNS),
            ("users", USER_COLUMNS),
        ):
            if table not in tables:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for column, definition in definitions.items():
                if column not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
