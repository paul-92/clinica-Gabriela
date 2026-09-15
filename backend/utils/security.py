import hashlib
import hmac
import os


DISABLED_CREDENTIAL_V1 = "!DISABLED_CREDENTIAL:v1!"


def is_disabled_credential(password_hash):
    return hmac.compare_digest(str(password_hash), DISABLED_CREDENTIAL_V1)


def hash_password(password):
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password, password_hash):
    if is_disabled_credential(password_hash):
        return False
    try:
        salt, expected = password_hash.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return hmac.compare_digest(digest, expected)
