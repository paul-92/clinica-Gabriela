import tkinter as tk
from tkinter import messagebox, ttk

from app.api.client import (
    ApiTimeoutError,
    BackendUnavailableError,
    DesktopApiClient,
    ForbiddenError,
    InvalidApiResponseError,
    InvalidCredentialsError,
    InvalidSessionError,
)
from app.views.main_view import MainView


class LoginView:
    def __init__(self, api_client: DesktopApiClient):
        self.root = tk.Tk()
        self.root.title("Marilia Gabriela Gaspar - Login")
        self.root.geometry("420x320")
        self.root.resizable(False, False)
        self.api_client = api_client
        self._build()

    def _build(self):
        frame = ttk.Frame(self.root, padding=28)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Marilia Gabriela Gaspar", font=("Segoe UI", 18, "bold")).pack(pady=(0, 22))
        ttk.Label(frame, text="Usuario").pack(anchor="w")
        self.username = ttk.Entry(frame)
        self.username.pack(fill="x", pady=(4, 12))
        ttk.Label(frame, text="Senha").pack(anchor="w")
        self.password = ttk.Entry(frame, show="*")
        self.password.pack(fill="x", pady=(4, 20))
        ttk.Button(frame, text="Entrar", command=self._login).pack(fill="x")

    def _login(self):
        password = self.password.get()
        try:
            identity = self.api_client.login(self.username.get(), password)
        except InvalidCredentialsError:
            self._show_error("Usuario ou senha invalidos.")
            return
        except BackendUnavailableError:
            self._show_error("Nao foi possivel conectar ao backend local.")
            return
        except ApiTimeoutError:
            self._show_error("O backend demorou demais para responder.")
            return
        except InvalidSessionError:
            self._show_error("A sessao nao e valida. Tente entrar novamente.")
            return
        except ForbiddenError:
            self._show_error("Acesso negado pelo backend.")
            return
        except InvalidApiResponseError:
            self._show_error("O backend retornou uma resposta inesperada.")
            return
        finally:
            password = None
            self.password.delete(0, tk.END)
        self.root.destroy()
        MainView(identity, self.api_client.session).mainloop()

    @staticmethod
    def _show_error(message):
        messagebox.showerror("Login", message)

    def run(self):
        self.root.mainloop()
