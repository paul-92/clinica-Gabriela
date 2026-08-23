import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.auth_controller import AuthController
from app.views.main_view import MainView


class LoginView:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Marilia Gabriela Gaspar - Login")
        self.root.geometry("420x320")
        self.root.resizable(False, False)
        self.controller = AuthController()
        self._build()

    def _build(self):
        frame = ttk.Frame(self.root, padding=28)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Marilia Gabriela Gaspar", font=("Segoe UI", 18, "bold")).pack(pady=(0, 22))
        ttk.Label(frame, text="Usuario").pack(anchor="w")
        self.username = ttk.Entry(frame)
        self.username.insert(0, "admin")
        self.username.pack(fill="x", pady=(4, 12))
        ttk.Label(frame, text="Senha").pack(anchor="w")
        self.password = ttk.Entry(frame, show="*")
        self.password.insert(0, "admin123")
        self.password.pack(fill="x", pady=(4, 20))
        ttk.Button(frame, text="Entrar", command=self._login).pack(fill="x")
        ttk.Label(frame, text="Usuarios exemplo: admin/admin123, marilia/marilia123, recepcao/recepcao123").pack(pady=(18, 0))

    def _login(self):
        user = self.controller.login(self.username.get(), self.password.get())
        if not user:
            messagebox.showerror("Login", "Usuario ou senha invalidos.")
            return
        self.root.destroy()
        MainView(user).mainloop()

    def run(self):
        self.root.mainloop()
