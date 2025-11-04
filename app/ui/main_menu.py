from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, Type

from app.services.api_client import ApiClient
from app.services.session import UserSession
from app.ui.users_window import UsersWindow
from app.ui.students_window import StudentsWindow
from app.ui.careers_window import CareersWindow
from app.ui.subjects_window import SubjectsWindow
from app.ui.teachers_window import TeachersWindow
from app.ui.schedules_window import SchedulesWindow
from app.ui.classrooms_window import ClassroomsWindow
from app.ui.groups_window import GroupsWindow

WindowType = Type[tk.Toplevel]


class MainMenu(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, padding=30)
        self.api = api
        self.session = session

        ttk.Label(self, text="Menú principal", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=(0, 20))

        self.buttons_container = ttk.Frame(self)
        self.buttons_container.grid(row=1, column=0, sticky="nsew")

        self._windows: Dict[str, tk.Toplevel] = {}
        self._build_buttons()

    def _build_buttons(self) -> None:
        role = self.session.role
        sections: Dict[str, WindowType] = {}

        if role == 'ADMIN':
            sections = {
                'Usuarios': UsersWindow,
                'Alumnos': StudentsWindow,
                'Carreras': CareersWindow,
                'Materias': SubjectsWindow,
                'Maestros': TeachersWindow,
                'Horarios': SchedulesWindow,
                'Salones': ClassroomsWindow,
                'Grupos': GroupsWindow
            }
        elif role == 'TEACHER':
            sections = {
                'Maestros': TeachersWindow
            }
        elif role == 'STUDENT':
            sections = {
                'Alumnos': StudentsWindow
            }

        for index, (label, window_class) in enumerate(sections.items()):
            button = ttk.Button(
                self.buttons_container,
                text=label,
                command=lambda wc=window_class, key=label: self._open_window(key, wc)
            )
            button.grid(row=index, column=0, sticky="ew", pady=5)

    def _open_window(self, name: str, window_class: WindowType) -> None:
        existing = self._windows.get(name)
        if existing and tk.Toplevel.winfo_exists(existing):
            existing.lift()
            return

        window = window_class(self.winfo_toplevel(), self.api, self.session)
        window.title(f"{name} - SIGUE")
        window.protocol("WM_DELETE_WINDOW", lambda w=window, key=name: self._close_window(key, w))
        self._windows[name] = window

    def _close_window(self, name: str, window: tk.Toplevel) -> None:
        if tk.Toplevel.winfo_exists(window):
            window.destroy()
        self._windows.pop(name, None)
