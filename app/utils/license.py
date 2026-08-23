import argparse
import base64
import hashlib
import hmac
import json
import secrets
from datetime import date, datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
LICENSE_PATH = BASE_DIR / "license.json"
LICENSE_SECRET_PATH = BASE_DIR / ".license_secret"


def _get_secret():
    if LICENSE_SECRET_PATH.exists():
        return LICENSE_SECRET_PATH.read_text(encoding="utf-8").strip()
    secret = secrets.token_hex(32)
    LICENSE_SECRET_PATH.write_text(secret, encoding="utf-8")
    return secret


def _signature_payload(data):
    clean_data = {key: value for key, value in data.items() if key != "signature"}
    return json.dumps(clean_data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_license(data):
    secret = _get_secret().encode("utf-8")
    digest = hmac.new(secret, _signature_payload(data), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8")


def verify_signature(data):
    signature = data.get("signature", "")
    if not signature:
        return False
    expected = sign_license(data)
    return hmac.compare_digest(signature, expected)


def create_license(customer, license_type="trial", days=14, expires_at=None):
    start_date = date.today()
    if expires_at:
        end_date = datetime.strptime(expires_at, "%Y-%m-%d").date()
    elif license_type == "full":
        end_date = date(2099, 12, 31)
    else:
        end_date = start_date + timedelta(days=days)

    data = {
        "customer": customer,
        "type": license_type,
        "issued_at": start_date.isoformat(),
        "expires_at": end_date.isoformat(),
        "machine_hint": "",
    }
    data["signature"] = sign_license(data)
    return data


def save_license(data, path=LICENSE_PATH):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_license(path=LICENSE_PATH):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def license_status(path=LICENSE_PATH):
    data = load_license(path)
    if not data:
        return {
            "valid": False,
            "reason": "missing",
            "message": "Licenca nao encontrada.",
            "customer": "",
            "type": "none",
            "expires_at": "",
            "days_left": 0,
        }

    if not verify_signature(data):
        return {
            "valid": False,
            "reason": "invalid_signature",
            "message": "Licenca invalida ou alterada.",
            "customer": data.get("customer", ""),
            "type": data.get("type", "unknown"),
            "expires_at": data.get("expires_at", ""),
            "days_left": 0,
        }

    try:
        expires_at = datetime.strptime(data["expires_at"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return {
            "valid": False,
            "reason": "invalid_date",
            "message": "Data da licenca invalida.",
            "customer": data.get("customer", ""),
            "type": data.get("type", "unknown"),
            "expires_at": data.get("expires_at", ""),
            "days_left": 0,
        }

    days_left = (expires_at - date.today()).days
    if days_left < 0:
        return {
            "valid": False,
            "reason": "expired",
            "message": "Periodo de teste ou licenca expirado.",
            "customer": data.get("customer", ""),
            "type": data.get("type", "unknown"),
            "expires_at": expires_at.isoformat(),
            "days_left": 0,
        }

    return {
        "valid": True,
        "reason": "active",
        "message": "Licenca ativa.",
        "customer": data.get("customer", ""),
        "type": data.get("type", "trial"),
        "expires_at": expires_at.isoformat(),
        "days_left": days_left,
    }


def assert_license():
    status = license_status()
    if not status["valid"]:
        raise RuntimeError(status["message"])
    return status


def main():
    parser = argparse.ArgumentParser(description="Gerador de licencas do sistema.")
    parser.add_argument("--customer", required=True, help="Nome do cliente.")
    parser.add_argument("--type", choices=["trial", "full"], default="trial", help="Tipo da licenca.")
    parser.add_argument("--days", type=int, default=14, help="Dias de teste.")
    parser.add_argument("--expires-at", help="Data final no formato YYYY-MM-DD.")
    args = parser.parse_args()

    data = create_license(args.customer, args.type, args.days, args.expires_at)
    save_license(data)
    print(f"Licenca gerada em: {LICENSE_PATH}")
    print(f"Cliente: {data['customer']}")
    print(f"Tipo: {data['type']}")
    print(f"Valida ate: {data['expires_at']}")


if __name__ == "__main__":
    main()
