"""Autoridade financeira legada explicitamente desativada pela SPEC-005."""

from app.repositories.finance_repository import LegacyFinanceAuthorityDisabled


class FinanceService:
    def __init__(self, session):
        del session
        raise LegacyFinanceAuthorityDisabled(
            "Calculo financeiro Tkinter desativado; use a API canonica."
        )

    def monthly_summary(self):
        raise LegacyFinanceAuthorityDisabled(
            "Calculo financeiro Tkinter desativado; use a API canonica."
        )
