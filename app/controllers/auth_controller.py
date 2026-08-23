from app.database.session import get_session
from app.services.auth_service import AuthService


class AuthController:
    def login(self, username, password):
        with get_session() as session:
            return AuthService(session).authenticate(username, password)
