from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession


class LoginFrame(tk.Frame): # Cambiado de ttk.Frame a tk.Frame para control total del fondo
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession, on_success: Callable[[dict], None]) -> None:
        
        # --- PALETA DE COLORES ---
        self.COLOR_BG = "#ecf0f1"        # Fondo gris claro (Nubes)
        self.COLOR_CARD_BG = "#ffffff"   # Fondo blanco de la tarjeta
        self.COLOR_PRIMARY = "#3498db"   # Azul "Universidad"
        self.COLOR_PRIMARY_HOVER = "#2980b9" # Azul más oscuro
        self.COLOR_TEXT_DARK = "#2c3e50"  # Texto oscuro
        self.COLOR_TEXT_LIGHT = "#ffffff"  # Texto blanco
        self.COLOR_BORDER = "#bdc3c7"     # Borde gris sutil
        # ---

        super().__init__(master, bg=self.COLOR_BG)
        self.api = api
        self.session = session
        self.on_success = on_success

        # Configurar el frame principal para centrar la tarjeta
        self.pack(fill=tk.BOTH, expand=True)
        
        # --- Tarjeta de Login (Login Card) ---
        # Usamos tk.Frame para control total de color
        self.login_card = tk.Frame(
            self, 
            bg=self.COLOR_CARD_BG, 
            padx=40, 
            pady=40,
            relief=tk.RIDGE,
            borderwidth=1,
            highlightbackground=self.COLOR_BORDER # Color del borde
        )
        # Posiciona la tarjeta en el centro absoluto de la ventana
        self.login_card.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # --- Contenido de la Tarjeta ---

        # Título
        tk.Label(
            self.login_card, 
            text="Iniciar Sesión", 
            font=("Segoe UI", 22, "bold"),
            bg=self.COLOR_CARD_BG,
            fg=self.COLOR_TEXT_DARK
        ).pack(pady=(0, 10))

        # Subtítulo
        tk.Label(
            self.login_card, 
            text="Sistema de Gestión Universitaria Estudiantil", 
            font=("Segoe UI", 11),
            bg=self.COLOR_CARD_BG,
            fg="#555555" # Gris para subtítulo
        ).pack(pady=(0, 25))

        # Formulario
        form = tk.Frame(self.login_card, bg=self.COLOR_CARD_BG)
        form.pack(fill=tk.X)
        form.columnconfigure(1, weight=1)

        tk.Label(
            form, 
            text="Usuario o correo", 
            font=("Segoe UI", 10),
            bg=self.COLOR_CARD_BG,
            fg=self.COLOR_TEXT_DARK
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(
            form, 
            textvariable=self.username_var, 
            font=("Segoe UI", 11),
            width=35 # Ancho del campo
        )
        self.username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        tk.Label(
            form, 
            text="Contraseña", 
            font=("Segoe UI", 10),
            bg=self.COLOR_CARD_BG,
            fg=self.COLOR_TEXT_DARK
        ).grid(row=2, column=0, sticky="w", pady=5)
        
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            form, 
            textvariable=self.password_var, 
            show="*", 
            font=("Segoe UI", 11),
            width=35
        )
        self.password_entry.grid(row=3, column=0, sticky="ew", pady=(0, 20))

        # --- Botón de Login (tk.Button para estilo) ---
        self.login_button = tk.Button(
            self.login_card, 
            text="Iniciar sesión",
            font=("Segoe UI", 12, "bold"),
            bg=self.COLOR_PRIMARY,
            fg=self.COLOR_TEXT_LIGHT,
            activebackground=self.COLOR_PRIMARY_HOVER,
            activeforeground=self.COLOR_TEXT_LIGHT,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._handle_login
        )
        self.login_button.pack(fill=tk.X)
        
        # Bind de eventos para el hover del botón
        self.login_button.bind("<Enter>", lambda e: self.login_button.config(bg=self.COLOR_PRIMARY_HOVER))
        self.login_button.bind("<Leave>", lambda e: self.login_button.config(bg=self.COLOR_PRIMARY))

        # --- Fin Contenido de la Tarjeta ---

        # Datos de prueba (opcional, pero útil como lo tenías)
        self.username_var.set("admin")
        self.password_var.set("Admin123")
        
        # Bind de 'Enter' a los campos de texto
        self.username_entry.bind("<Return>", lambda e: self._handle_login())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())


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