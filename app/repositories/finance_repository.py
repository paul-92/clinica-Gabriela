"""Compatibilidade nominal do legado; persistencia financeira local desativada."""


class LegacyFinanceAuthorityDisabled(RuntimeError):
    pass


class FinanceRepository:
    def __init__(self, session):
        del session
        raise LegacyFinanceAuthorityDisabled(
            "Persistencia financeira Tkinter desativada; use a API canonica."
        )

    def payments(self):
        raise LegacyFinanceAuthorityDisabled("Leitura financeira local desativada.")

    def expenses(self):
        raise LegacyFinanceAuthorityDisabled("Leitura financeira local desativada.")
