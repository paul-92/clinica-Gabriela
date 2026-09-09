from tkinter import ttk

from app.views.base import AppWindow
from app.views.pages import (
    AgendaPage,
    DashboardPage,
    FinancePage,
    PatientsPage,
    PlaceholderPage,
    ReportsPage,
    SettingsPage,
)


ROLE_MODULES = {
    "admin": {"settings"},
    "psychologist": {"clinical_records"},
    "reception": set(),
}


def can_access_module(role, module):
    return module in ROLE_MODULES.get(role, set())


class MainView(AppWindow):
    def __init__(self, user):
        super().__init__("Marilia Gabriela Gaspar")
        self.user = user
        self._build()

    def _build(self):
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Marilia Gabriela Gaspar | Psicologa", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text=f"{self.user.name} - {self.user.role}").pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        pages = [
            ("Dashboard", DashboardPage(notebook)),
            ("Pacientes", PatientsPage(notebook)),
            ("Psicologos", PlaceholderPage(notebook, "Cadastro de psicologos")),
            ("Agenda", AgendaPage(notebook)),
            ("Financeiro", FinancePage(notebook)),
            ("Relatorios", ReportsPage(notebook)),
        ]
        if can_access_module(self.user.role, "clinical_records"):
            pages.insert(4, ("Prontuario", PlaceholderPage(notebook, "Prontuario e evolucao clinica")))
        if can_access_module(self.user.role, "settings"):
            pages.append(("Configuracoes", SettingsPage(notebook)))
        for title, page in pages:
            notebook.add(page, text=title)
