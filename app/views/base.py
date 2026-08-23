import tkinter as tk
from tkinter import ttk


class AppWindow(tk.Tk):
    def __init__(self, title):
        super().__init__()
        self.title(title)
        self.geometry("1100x720")
        self.minsize(960, 620)
        self.configure(bg="#f5f7fb")
        self._style()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("Panel.TFrame", background="#ffffff", borderwidth=1, relief="solid")
        style.configure("TLabel", background="#f5f7fb", foreground="#20242a", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("CardTitle.TLabel", background="#ffffff", font=("Segoe UI", 11, "bold"))
        style.configure("CardValue.TLabel", background="#ffffff", font=("Segoe UI", 20, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
