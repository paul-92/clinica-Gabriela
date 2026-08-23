import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.appointment_controller import AppointmentController
from app.controllers.dashboard_controller import DashboardController
from app.controllers.finance_controller import FinanceController
from app.controllers.patient_controller import PatientController
from app.reports.monthly_finance_report import build_monthly_finance_report


class DashboardPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=16)
        self.controller = DashboardController()
        self._build()

    def _build(self):
        summary = self.controller.summary()
        values = [
            ("Pacientes", summary["patients_count"]),
            ("Atendimentos hoje", summary["today_appointments"]),
            ("Pendente", f"R$ {summary['finance']['pending']:.2f}"),
            ("Saldo", f"R$ {summary['finance']['balance']:.2f}"),
        ]
        for index, (title, value) in enumerate(values):
            card = ttk.Frame(self, style="Panel.TFrame", padding=18)
            card.grid(row=0, column=index, sticky="nsew", padx=6, pady=6)
            ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(card, text=value, style="CardValue.TLabel").pack(anchor="w", pady=(10, 0))
            self.columnconfigure(index, weight=1)


class PatientsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=16)
        self.controller = PatientController()
        self._build()
        self.refresh()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))
        self.search = ttk.Entry(top)
        self.search.pack(side="left", fill="x", expand=True)
        ttk.Button(top, text="Buscar", command=self.refresh).pack(side="left", padx=8)
        ttk.Button(top, text="Novo paciente", command=self.open_new_patient).pack(side="left")

        columns = ("nome", "cpf", "telefone", "email", "status")
        self.table = ttk.Treeview(self, columns=columns, show="headings", height=18)
        for column in columns:
            self.table.heading(column, text=column.title())
            self.table.column(column, width=160)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        for item in self.table.get_children():
            self.table.delete(item)
        for patient in self.controller.list_patients(self.search.get()):
            self.table.insert(
                "",
                "end",
                values=(patient.full_name, patient.cpf, patient.phone, patient.email, "Ativo" if patient.active else "Inativo"),
            )

    def open_new_patient(self):
        window = tk.Toplevel(self)
        window.title("Cadastro de paciente")
        window.geometry("520x560")
        fields = [
            ("full_name", "Nome completo"),
            ("cpf", "CPF"),
            ("birth_date", "Data de nascimento (YYYY-MM-DD)"),
            ("phone", "Telefone"),
            ("email", "E-mail"),
            ("address", "Endereco"),
            ("emergency_contact", "Contato de emergencia"),
            ("notes", "Observacoes"),
        ]
        entries = {}
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)
        for key, label in fields:
            ttk.Label(frame, text=label).pack(anchor="w")
            entry = ttk.Entry(frame)
            entry.pack(fill="x", pady=(3, 9))
            entries[key] = entry

        def save():
            data = {key: entry.get() for key, entry in entries.items()}
            data["active"] = True
            try:
                self.controller.create_patient(data)
            except Exception as exc:
                messagebox.showerror("Paciente", f"Nao foi possivel salvar: {exc}")
                return
            window.destroy()
            self.refresh()

        ttk.Button(frame, text="Salvar", command=save).pack(fill="x", pady=(10, 0))


class AgendaPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=16)
        self.controller = AppointmentController()
        self._build()

    def _build(self):
        ttk.Label(self, text="Atendimentos do dia", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        columns = ("horario", "paciente", "psicologo", "status", "observacoes")
        table = ttk.Treeview(self, columns=columns, show="headings", height=20)
        for column in columns:
            table.heading(column, text=column.title())
            table.column(column, width=170)
        table.pack(fill="both", expand=True)
        for appointment in self.controller.today():
            table.insert(
                "",
                "end",
                values=(
                    appointment.scheduled_at.strftime("%H:%M"),
                    appointment.patient.full_name,
                    appointment.psychologist.full_name,
                    appointment.status,
                    appointment.notes,
                ),
            )


class FinancePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=16)
        self.controller = FinanceController()
        self._build()

    def _build(self):
        summary = self.controller.summary()
        text = (
            f"Sessoes pagas: R$ {summary['paid']:.2f}\n"
            f"Sessoes pendentes: R$ {summary['pending']:.2f}\n"
            f"Despesas: R$ {summary['expenses']:.2f}\n"
            f"Saldo mensal: R$ {summary['balance']:.2f}"
        )
        ttk.Label(self, text="Financeiro", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(self, text=text, font=("Segoe UI", 12)).pack(anchor="w", pady=14)


class ReportsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=16)
        self._build()

    def _build(self):
        ttk.Label(self, text="Relatorios", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        report = tk.Text(self, height=12)
        report.pack(fill="both", expand=True, pady=12)
        report.insert("1.0", build_monthly_finance_report())


class SettingsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=16)
        ttk.Label(self, text="Configuracoes do sistema", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(self, text="Backup local, dados da clinica e parametros padrao ficam nesta area.").pack(anchor="w", pady=12)


class PlaceholderPage(ttk.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, padding=16)
        ttk.Label(self, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(self, text="Modulo estruturado para evolucao nas proximas etapas.").pack(anchor="w", pady=12)
