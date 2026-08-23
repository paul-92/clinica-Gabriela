from app.database.seed import seed_database
from app.database.migrations import run_light_migrations
from app.database.session import init_db
from app.utils.license import assert_license
from app.views.login_view import LoginView


def main():
    assert_license()
    init_db()
    run_light_migrations()
    seed_database()
    LoginView().run()


if __name__ == "__main__":
    main()
