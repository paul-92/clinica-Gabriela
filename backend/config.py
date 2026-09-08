import os


AUTH_SECRET_ENV = "AUTH_SECRET"


def get_auth_secret() -> str:
    secret = os.getenv(AUTH_SECRET_ENV)

    if not secret:
        raise RuntimeError(
            f"{AUTH_SECRET_ENV} environment variable is required"
        )

    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError(
            f"{AUTH_SECRET_ENV} must contain at least 32 bytes"
        )

    return secret
