from __future__ import annotations

import tkinter as tk
from tkinter import ttk, TclError
from typing import Dict, Type

from app.services.api_client import ApiClient
from app.services.session import UserSession

# Importamos las clases de las ventanas
from app.ui.users_window import UsersWindow
from app.ui.students_window import StudentsWindow
from app.ui.careers_window import CareersWindow
from app.ui.subjects_window import SubjectsWindow
from app.ui.teachers_window import TeachersWindow
from app.ui.schedules_window import SchedulesWindow
from app.ui.classrooms_window import ClassroomsWindow
from app.ui.groups_window import GroupsWindow

# CAMBIO IMPORTANTE: Ahora esperamos que las "ventanas" sean Frames
WindowType = Type[ttk.Frame] 


class MainMenu(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master)
        self.api = api
        self.session = session
        self.master = master
        
        # --- PALETA DE COLORES ---
        self.COLOR_SIDENAV = "#2c3e50"
        self.COLOR_CONTENT_BG = "#ecf0f1"
        self.COLOR_BTN_HOVER = "#34495e"
        self.COLOR_TEXT_LIGHT = "#ffffff"
        self.COLOR_TEXT_DARK = "#2c3e50"
        
        # --- Estilos ---
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except TclError:
            pass 

        self.style.configure(
            'Sidenav.TButton',
            font=('Segoe UI', 11, 'bold'), padding=(20, 12), borderwidth=0, relief='flat',
            background=self.COLOR_SIDENAV, foreground=self.COLOR_TEXT_LIGHT
        )
        self.style.map(
            'Sidenav.TButton',
            background=[('active', self.COLOR_BTN_HOVER), ('pressed', self.COLOR_BTN_HOVER)],
            foreground=[('!disabled', self.COLOR_TEXT_LIGHT)]
        )
        # Nuevo estilo para los frames de contenido
        self.style.configure('Content.TFrame', background=self.COLOR_CONTENT_BG)

        # --- Layout Principal ---
        self.pack(fill=tk.BOTH, expand=True)

        self.sidenav_frame = tk.Frame(self, bg=self.COLOR_SIDENAV, width=250)
        self.sidenav_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidenav_frame.pack_propagate(False) 

        self.content_frame = tk.Frame(self, bg=self.COLOR_CONTENT_BG)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Variable para guardar el frame actual ---
        self.current_content_frame: tk.Widget | None = None

        self._build_sidenav()
        self._show_welcome_screen() # Mostrar la bienvenida al inicio

    # --- Funciones de Hover (sin cambios) ---
    def on_enter(self, button: tk.Button) -> None:
        button.config(bg=self.COLOR_BTN_HOVER)
    def on_leave(self, button: tk.Button) -> None:
        button.config(bg=self.COLOR_SIDENAV)
    # ---

    def _build_sidenav(self) -> None:
        tk.Label(
            self.sidenav_frame, text="SIGUE", font=('Segoe UI', 20, 'bold'),
            bg=self.COLOR_SIDENAV, fg=self.COLOR_TEXT_LIGHT, anchor='w'
        ).pack(pady=(20, 25), padx=25, fill='x')
        
        icon_map = {
            'Usuarios': '👤', 'Alumnos': '🧑‍🎓', 'Carreras': '📚', 'Materias': '📖',
            'Maestros': '👨‍🏫', 'Horarios': '🕒', 'Salones': '🚪', 'Grupos': '👥'
        }

        role = self.session.role
        sections: Dict[str, WindowType] = {}

        if role == 'ADMIN':
            sections = {
                'Usuarios': UsersWindow, 'Alumnos': StudentsWindow, 'Carreras': CareersWindow,
                'Materias': SubjectsWindow, 'Maestros': TeachersWindow, 'Horarios': SchedulesWindow,
                'Salones': ClassroomsWindow, 'Grupos': GroupsWindow
            }
        elif role == 'TEACHER':
            sections = {'Maestros': TeachersWindow}
        elif role == 'STUDENT':
            sections = {'Alumnos': StudentsWindow}

        # --- BOTÓN DE INICIO (NUEVO) ---
        home_button = tk.Button(
            self.sidenav_frame, text="  🏠   Inicio", font=('Segoe UI', 11, 'bold'),
            bg=self.COLOR_SIDENAV, fg=self.COLOR_TEXT_LIGHT,
            activebackground=self.COLOR_BTN_HOVER, activeforeground=self.COLOR_TEXT_LIGHT,
            relief='flat', bd=0, justify=tk.LEFT, anchor='w', cursor="hand2",
            command=self._show_welcome_screen # Llama a la pantalla de bienvenida
        )
        home_button.pack(fill=tk.X, pady=4, padx=15)
        home_button.bind("<Enter>", lambda e, b=home_button: self.on_enter(b))
        home_button.bind("<Leave>", lambda e, b=home_button: self.on_leave(b))
        # ---

        for label, window_class in sections.items():
            icon = icon_map.get(label, '🔹')
            button_text = f"  {icon}   {label}"
            
            button = tk.Button(
                self.sidenav_frame, text=button_text, font=('Segoe UI', 11, 'bold'),
                bg=self.COLOR_SIDENAV, fg=self.COLOR_TEXT_LIGHT,
                activebackground=self.COLOR_BTN_HOVER, activeforeground=self.COLOR_TEXT_LIGHT,
                relief='flat', bd=0, justify=tk.LEFT, anchor='w', cursor="hand2",
                command=lambda wc=window_class, key=label: self._load_module(key, wc)
            )
            button.pack(fill=tk.X, pady=4, padx=15)
            
            button.bind("<Enter>", lambda e, b=button: self.on_enter(b))
            button.bind("<Leave>", lambda e, b=button: self.on_leave(b))

    def _clear_content_area(self) -> None:
        """Destruye el frame de contenido actual."""
        if self.current_content_frame:
            self.current_content_frame.destroy()
            self.current_content_frame = None

    def _show_welcome_screen(self) -> None:
        """Muestra la pantalla de bienvenida en el área de contenido."""
        self._clear_content_area()
        
        # El frame de bienvenida se convierte en el frame actual
        self.current_content_frame = tk.Frame(self.content_frame, bg=self.COLOR_CONTENT_BG)
        self.current_content_frame.pack(expand=True)

        try:
            user_name = self.session.user.get('nombre', 'Usuario')
            first_name = user_name.split(' ')[0]
        except Exception:
            first_name = "Usuario"

        tk.Label(
            self.current_content_frame, text=f"¡Bienvenido, {first_name}!",
            bg=self.COLOR_CONTENT_BG, fg=self.COLOR_TEXT_DARK, font=('Segoe UI', 28, 'bold')
        ).pack(pady=10)
        
        tk.Label(
            self.current_content_frame, text="Selecciona una opción del menú lateral para comenzar.",
            bg=self.COLOR_CONTENT_BG, fg="#555555", font=('Segoe UI', 14)
        ).pack()

    def _load_module(self, name: str, module_class: WindowType) -> None:
        """Carga un módulo (Frame) en el área de contenido."""
        self._clear_content_area()
        
        # Crea una instancia del frame del módulo (ej. ClassroomsWindow)
        # y lo coloca dentro de self.content_frame
        frame = module_class(self.content_frame, self.api, self.session)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Guarda una referencia al nuevo frame para poder destruirlo después
        self.current_content_frame = frame