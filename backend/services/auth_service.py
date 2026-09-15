from backend.repositories.user_repository import UserRepository
from backend.utils.security import is_disabled_credential, verify_password


class AuthService:
    def __init__(self, db):
        self.users = UserRepository(db)

    def authenticate(self, username, password):
        user = self.users.get_by_username(username.strip())
        if (
            not user
            or user.password_reset_required
            or is_disabled_credential(user.password_hash)
            or not verify_password(password, user.password_hash)
        ):
            return None
        return user
