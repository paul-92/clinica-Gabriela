from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.session import Base
from backend.models.user import User
from backend.services.auth_service import AuthService
from backend.utils.security import DISABLED_CREDENTIAL_V1, hash_password, verify_password


def make_session():
    engine = create_engine("sqlite:///:memory:")
    from backend.models import (  # noqa: F401
        appointment,
        clinical_record,
        finance,
        patient,
        psychologist,
        settings,
        user,
    )
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


def test_user_requiring_password_reset_cannot_authenticate():
    db = make_session()
    user = User(
        name="Usuario Reset",
        username="reset",
        password_hash=hash_password("senha123"),
        role="reception",
        active=True,
        password_reset_required=True,
    )
    db.add(user)
    db.commit()

    assert AuthService(db).authenticate("reset", "senha123") is None


def test_disabled_credential_never_authenticates_any_password():
    for password in ("", "senha123", DISABLED_CREDENTIAL_V1, "qualquer-outra"):
        assert verify_password(password, DISABLED_CREDENTIAL_V1) is False


def test_inconsistent_disabled_credential_without_reset_fails_closed():
    db = make_session()
    user = User(
        name="Usuario Inconsistente",
        username="inconsistente",
        password_hash=DISABLED_CREDENTIAL_V1,
        role="reception",
        active=True,
        password_reset_required=False,
    )
    db.add(user)
    db.commit()

    assert AuthService(db).authenticate("inconsistente", "qualquer-senha") is None
