from app.utils.security import hash_password, verify_password


def test_password_hash_verification():
    hashed = hash_password("senha-segura")
    assert verify_password("senha-segura", hashed)
    assert not verify_password("outra", hashed)
