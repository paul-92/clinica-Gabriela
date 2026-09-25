"""Identidade técnica do legado financeiro D005-10 (sem labels R1–R6)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


CANONICALIZATION_VERSION = "spec005-row-v1"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_fingerprint(entity_type: str, row: dict) -> str:
    """Hash SHA-256 de todos os campos originais, com tipos e nomes ordenados.

    O domínio permite apenas valores SQLite primitivos. O conteúdo original nunca
    é retornado ou registrado; a versão impede ambiguidades futuras de encoding.
    """
    if entity_type not in {"payment", "expense"} or not isinstance(row.get("id"), int):
        raise ValueError("identidade financeira inválida")
    values = []
    for key in sorted(row):
        value = row[key]
        if value is None:
            encoded = ["null", None]
        elif isinstance(value, bool):
            encoded = ["integer", int(value)]
        elif isinstance(value, int):
            encoded = ["integer", value]
        elif isinstance(value, float):
            encoded = ["real", value.hex()]
        elif isinstance(value, str):
            encoded = ["text", value]
        elif isinstance(value, bytes):
            encoded = ["blob", value.hex()]
        else:
            raise ValueError("tipo SQLite não suportado")
        values.append([key, *encoded])
    payload = json.dumps([CANONICALIZATION_VERSION, entity_type, values],
                         ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_rows(connection: sqlite3.Connection, table: str) -> list[dict]:
    if table not in {"payments", "expenses"}:
        raise ValueError("tabela financeira inválida")
    cursor = connection.execute(f'SELECT * FROM "{table}"')
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, values)) for values in cursor.fetchall()]
