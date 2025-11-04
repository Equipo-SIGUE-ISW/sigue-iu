from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession


class LoginFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession, on_success: Callable[[dict], None]) -> None:
        super().__init__(master, padding=40)
        self.api = api
        self.session = session
        self.on_success = on_success

        self.columnconfigure(0, weight=1)

        ttk.Label(self, text="Sistema de Gestión Universitaria Estudiantil", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=(0, 20))

        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Usuario o correo").grid(row=0, column=0, sticky="w", pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.username_var).grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Contraseña").grid(row=1, column=0, sticky="w", pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.password_var, show="*").grid(row=1, column=1, sticky="ew", pady=5)

        login_button = ttk.Button(self, text="Iniciar sesión", command=self._handle_login)
        login_button.grid(row=2, column=0, pady=(20, 0), sticky="ew")

        self.username_var.set("admin")
        self.password_var.set("Admin123")

    def _handle_login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Datos incompletos", "Ingresa usuario y contraseña.")
            return

        try:
            result = self.api.login(username=username, password=password)
        except ApiError as error:
            messagebox.showerror("Error de autenticación", error.message)
            return
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", f"Ocurrió un problema: {error}")
            return

        self.session.token = result.get("token")
        self.session.user = result.get("user", {})
        self.on_success(result.get("user", {}))
