from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from app.config import CONFIG
from app.services.api_client import ApiClient
from app.services.session import UserSession
from app.ui.login_view import LoginFrame
from app.ui.main_menu import MainMenu


class SchoolControlApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sistema de Gestión Universitaria Estudiantil")
        self.geometry('1024x720')
        self.api = ApiClient(CONFIG.api_base_url)
        self.session = UserSession()
        self.current_view: tk.Widget | None = None

        self._show_login()

    def _clear_view(self) -> None:
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

    def _show_login(self) -> None:
        self._clear_view()
        login_frame = LoginFrame(self, self.api, self.session, self._on_login_success)
        login_frame.pack(fill=tk.BOTH, expand=True)
        self.current_view = login_frame

    def _show_main_menu(self) -> None:
        self._clear_view()
        menu = MainMenu(self, self.api, self.session)
        menu.pack(fill=tk.BOTH, expand=True)
        self.current_view = menu
        self._build_menu_bar()

    def _build_menu_bar(self) -> None:
        menubar = tk.Menu(self)
        account_menu = tk.Menu(menubar, tearoff=0)
        account_menu.add_command(label="Cerrar sesión", command=self._logout)
        menubar.add_cascade(label="Cuenta", menu=account_menu)
        self.config(menu=menubar)

    def _on_login_success(self, user: dict) -> None:
        if not user:
            messagebox.showerror("Error", "No se pudo obtener información del usuario")
            return
        self.session.user = user
        self._show_main_menu()

    def _logout(self) -> None:
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar la sesión actual?"):
            self.session.clear()
            self.api.set_token(None)
            self.config(menu=None)
            self._show_login()


def main() -> None:
    app = SchoolControlApp()
    app.mainloop()


if __name__ == '__main__':
    main()
