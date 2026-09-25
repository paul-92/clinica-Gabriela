from sqlalchemy.exc import IntegrityError

from backend.models.user import User, UserRole
from backend.repositories.user_repository import UserRepository
from backend.services.errors import ConflictError, NotFoundError
from backend.utils.security import hash_password


class UserManagementService:
    def __init__(self, db):
        self.db = db
        self.users = UserRepository(db)

    @staticmethod
    def _validate_role(role):
        allowed = {item.value for item in UserRole}
        if role not in allowed:
            raise ValueError("Perfil de usuario invalido.")

    @staticmethod
    def _clean_text(value):
        return value.strip() if isinstance(value, str) else value

    def list_users(self):
        return self.users.list_for_administration()

    def create_user(self, data):
        values = data.copy()
        values["name"] = self._clean_text(values["name"])
        values["username"] = self._clean_text(values["username"])
        self._validate_role(values["role"])
        if not values["name"] or not values["username"]:
            raise ValueError("Nome e usuario sao obrigatorios.")
        if self.users.get_by_username_including_inactive(values["username"]):
            raise ConflictError("Nao foi possivel criar o usuario.")
        password = values.pop("password")
        values["password_hash"] = hash_password(password)
        try:
            return self.users.create(values)
        except IntegrityError as exc:
            raise ConflictError("Nao foi possivel criar o usuario.") from exc

    def update_user(self, user_id, data, actor_id):
        user = self.users.get_by_id_for_administration(user_id)
        if user is None:
            raise NotFoundError("Usuario nao encontrado.")
        changes = {key: self._clean_text(value) for key, value in data.items() if value is not None}
        if "role" in changes:
            self._validate_role(changes["role"])
        if "username" in changes and not changes["username"]:
            raise ValueError("Usuario e obrigatorio.")
        if "name" in changes and not changes["name"]:
            raise ValueError("Nome e obrigatorio.")
        if changes.get("active") is False and user.id == actor_id:
            raise ValueError("Nao e permitido desativar o proprio usuario.")
        if "username" in changes:
            other = self.users.get_by_username_including_inactive(changes["username"])
            if other is not None and other.id != user.id:
                raise ConflictError("Nao foi possivel atualizar o usuario.")
        try:
            return self.users.update(user, changes)
        except IntegrityError as exc:
            raise ConflictError("Nao foi possivel atualizar o usuario.") from exc
