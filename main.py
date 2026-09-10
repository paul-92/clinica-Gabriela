from app.database.seed import seed_database
from app.database.migrations import run_light_migrations
from app.database.session import init_db
from app.api.client import DesktopApiClient, DesktopSession
from app.utils.license import assert_license
from app.views.login_view import LoginView
from backend.supervisor import BackendAlreadyRunning, BackendSupervisor


def main():
    assert_license()
    init_db()
    run_light_migrations()
    seed_database()
    supervisor = BackendSupervisor()
    owns_backend = False
    try:
        try:
            supervisor.start()
            owns_backend = True
        except BackendAlreadyRunning:
            pass
        session = DesktopSession()
        LoginView(DesktopApiClient(session=session)).run()
    finally:
        if owns_backend:
            supervisor.stop()


if __name__ == "__main__":
    main()
