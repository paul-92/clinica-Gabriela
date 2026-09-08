from backend.models.user import User
from backend.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, User)

    def get_by_username(self, username):
        return (
            self.db.query(User)
            .filter(
                User.username == username,
                User.active.is_(True),
            )
            .first()
        )

    def get_active_by_id(self, user_id):
        return (
            self.db.query(User)
            .filter(
                User.id == user_id,
                User.active.is_(True),
            )
            .first()
        )
