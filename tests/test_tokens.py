from datetime import timedelta

import jwt
import pytest

from backend.utils.tokens import create_access_token, decode_access_token


SECRET = "segredo-de-teste-com-32-bytes-minimo-001"
OTHER_SECRET = "outro-segredo-com-32-bytes-minimo-002"


def test_valid_token_can_be_decoded():
    token = create_access_token(
        subject="1",
        role="psychologist",
        secret=SECRET,
    )

    payload = decode_access_token(token, SECRET)

    assert payload["sub"] == "1"
    assert payload["role"] == "psychologist"


def test_tampered_token_is_rejected():
    token = create_access_token(
        subject="1",
        role="psychologist",
        secret=SECRET,
    )

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token, OTHER_SECRET)


def test_expired_token_is_rejected():
    token = create_access_token(
        subject="1",
        role="psychologist",
        secret=SECRET,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, SECRET)
