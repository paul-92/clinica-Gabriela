from fastapi import HTTPException


def parse_if_match(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = value.strip().removeprefix("W/").strip('"')
    try:
        return int(cleaned)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="If-Match invalido.") from exc
