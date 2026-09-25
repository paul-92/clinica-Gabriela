from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError


class ConflictError(Exception):
    pass


class NotFoundError(Exception):
    pass


def translate_integrity_error(db, exc: IntegrityError):
    db.rollback()
    message = str(getattr(exc, "orig", "")).lower()
    if "unique" in message:
        detail = "Registro duplicado para uma identidade unica."
    elif "foreign key" in message:
        detail = "Operacao conflitante com referencias existentes."
    elif "not null" in message or "check" in message:
        detail = "Operacao conflitante com as regras de integridade."
    else:
        detail = "Conflito de integridade de dados."
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
