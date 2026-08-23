from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, User)

    def get_by_username(self, username):
        return self.session.query(User).filter(User.username == username, User.active.is_(True)).first()
