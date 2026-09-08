from fastapi import Depends, HTTPException, status

from backend.api.routes.auth import get_current_user
from backend.models.user import User


def require_psychologist(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "psychologist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
