from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.session import Base
from backend.models.user import User
from backend.services.auth_service import AuthService
from backend.utils.security import hash_password


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_active_user_can_authenticate():
    db = make_session()

    user = User(
        name="Usuario Ativo",
        username="ativo",
        password_hash=hash_password("senha123"),
        role="reception",
        active=True,
    )

    db.add(user)
    db.commit()

    authenticated = AuthService(db).authenticate("ativo", "senha123")

    assert authenticated is not None
    assert authenticated.username == "ativo"


def test_inactive_user_cannot_authenticate():
    db = make_session()

    user = User(
        name="Usuario Inativo",
        username="inativo",
        password_hash=hash_password("senha123"),
        role="reception",
        active=False,
    )

    db.add(user)
    db.commit()

    authenticated = AuthService(db).authenticate("inativo", "senha123")

    assert authenticated is None
