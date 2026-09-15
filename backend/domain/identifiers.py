import re


def normalize_cpf(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11 or len(set(digits)) == 1:
        raise ValueError("CPF invalido.")
    for position in (9, 10):
        total = sum(int(digits[index]) * (position + 1 - index) for index in range(position))
        digit = (total * 10) % 11
        if digit == 10:
            digit = 0
        if digit != int(digits[position]):
            raise ValueError("CPF invalido.")
    return digits


def normalize_crp_part(value: str | None, label: str) -> str | None:
    if value is None or not value.strip():
        return None
    digits = re.sub(r"\D", "", value)
    if not digits:
        raise ValueError(f"{label} do CRP invalido.")
    return digits


def normalize_crp(region: str | None, number: str | None) -> tuple[str | None, str | None]:
    normalized_region = normalize_crp_part(region, "Regional")
    normalized_number = normalize_crp_part(number, "Numero")
    if (normalized_region is None) != (normalized_number is None):
        raise ValueError("Regional e numero do CRP devem ser informados juntos.")
    return normalized_region, normalized_number
