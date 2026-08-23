from backend.repositories.user_repository import UserRepository
from backend.utils.security import verify_password


class AuthService:
    def __init__(self, db):
        self.users = UserRepository(db)

    def authenticate(self, username, password):
        user = self.users.get_by_username(username.strip())
        if not user or not verify_password(password, user.password_hash):
            return None
        return user
