from sqlalchemy import create_engine, inspect, text

from backend.database.migrations import run_light_migrations


def test_users_migration_adds_safe_password_reset_state(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text("INSERT INTO users (id) VALUES (1)"))

    run_light_migrations(engine)
    run_light_migrations(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    with engine.connect() as connection:
        reset_required = connection.execute(
            text("SELECT password_reset_required FROM users WHERE id = 1")
        ).scalar_one()
    assert "password_reset_required" in columns
    assert reset_required == 0
