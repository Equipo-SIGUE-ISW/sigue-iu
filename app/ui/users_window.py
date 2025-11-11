from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, Optional
import re  # <--- IMPORTADO PARA VALIDAR EMAIL

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession
# from app.ui.base_window import ModuleWindow # Ya no se usa

# CAMBIO 1: Heredar de ttk.Frame
class UsersWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, padding=20) # CAMBIO 2: Aplicar padding aquí
        self.api = api
        self.session = session
        self.is_admin = session.role == 'ADMIN'
        self.current_user_id: Optional[int] = None
        
        # Expresión regular para validar email
        self.EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        # --- MEJORA ESTÉTICA: Paleta de Colores ---
        self.COLOR_BG = "#ecf0f1"
        self.COLOR_PRIMARY = "#3498db"
        self.COLOR_DANGER = "#e74c3c"
        self.COLOR_TEXT_DARK = "#2c3e50"
        self.COLOR_WHITE = "#ffffff"
        self.COLOR_GRAY_BORDER = "#bdc3c7"

        # --- MEJORA ESTÉTICA: Aplicar Estilos ---
        self.style = ttk.Style(self)
        self.style.configure('Content.TFrame', background=self.COLOR_BG)
        self.configure(style='Content.TFrame')
        self.style.configure('Content.TLabel', background=self.COLOR_BG, foreground=self.COLOR_TEXT_DARK, font=('Segoe UI', 10))
        self.style.configure('Form.TLabelframe', background=self.COLOR_BG, relief="solid", borderwidth=1, bordercolor=self.COLOR_GRAY_BORDER)
        self.style.configure('Form.TLabelframe.Label', background=self.COLOR_BG, foreground=self.COLOR_TEXT_DARK, font=('Segoe UI', 12, 'bold'))
        self.style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), background=self.COLOR_PRIMARY, foreground=self.COLOR_WHITE)
        self.style.map('Primary.TButton', background=[('active', '#2980b9'), ('pressed', '#2980b9')])
        self.style.configure('Danger.TButton', font=('Segoe UI', 10, 'bold'), background=self.COLOR_DANGER, foreground=self.COLOR_WHITE)
        self.style.map('Danger.TButton', background=[('active', '#c0392b'), ('pressed', '#c0392b')])

        # CAMBIO 3: Layout directo en el frame
        self.pack(fill=tk.BOTH, expand=True)
        self.columnconfigure(0, weight=1) # Columna 0 se expande

        # Título del Módulo
        title_text = "Gestión de Usuarios" if self.is_admin else "Mi Perfil de Usuario"
        ttk.Label(self, text=title_text, font=("Segoe UI", 16, "bold"), background=self.COLOR_BG).grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        row_offset = 1 # Para saber en qué fila empezar
        
        if self.is_admin:
            self._build_search(self)
            self._build_tree(self)
            row_offset = 3 # El form irá después de la búsqueda y la tabla
        
        self.rowconfigure(row_offset - 1, weight=1) # La tabla o el form se expanden
        self._build_form(self, form_row=row_offset)

        self._reset() # Usamos _reset para setear el estado inicial

        if self.is_admin:
            self._load_users()
        else:
            self._load_self()

    def _build_search(self, container: ttk.Frame) -> None:
        search_frame = ttk.Frame(container, style='Content.TFrame')
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(search_frame, text="Buscar por ID:", style='Content.TLabel').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=15)
        search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Buscar", command=self._search_by_id, style='Primary.TButton').pack(side=tk.LEFT)

    def _build_tree(self, container: ttk.Frame) -> None:
        tree_container = ttk.Frame(container, style='Content.TFrame')
        tree_container.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)
        
        columns = ("id", "email", "username", "role")
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=8)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.heading('id', text='ID'); self.tree.column('id', width=50, stretch=False)
        self.tree.heading('email', text='Email'); self.tree.column('email', width=250)
        self.tree.heading('username', text='Usuario'); self.tree.column('username', width=200)
        self.tree.heading('role', text='Rol'); self.tree.column('role', width=100)
        
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

    def _build_form(self, container: ttk.Frame, form_row: int) -> None:
        form = ttk.LabelFrame(container, text="Datos del usuario", style='Form.TLabelframe', padding=15)
        form.grid(row=form_row, column=0, pady=10, sticky="nsew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID", style='Content.TLabel').grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.id_entry = ttk.Entry(form, textvariable=self.id_var, state='readonly')
        self.id_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        self.email_var = tk.StringVar()
        ttk.Label(form, text="Email", style='Content.TLabel').grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.email_entry = ttk.Entry(form, textvariable=self.email_var)
        self.email_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        self.username_var = tk.StringVar()
        ttk.Label(form, text="Nombre de usuario", style='Content.TLabel').grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.username_entry = ttk.Entry(form, textvariable=self.username_var)
        self.username_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        self.password_var = tk.StringVar()
        ttk.Label(form, text="Contraseña", style='Content.TLabel').grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.password_entry = ttk.Entry(form, textvariable=self.password_var, show='*')
        self.password_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        self.password_entry.bind("<FocusIn>", lambda e: self.password_entry.config(show=''))
        self.password_entry.bind("<FocusOut>", lambda e: self.password_entry.config(show='*') if not self.password_var.get() else None)


        ttk.Label(form, text="Perfil", style='Content.TLabel').grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(form, textvariable=self.role_var, values=['ADMIN', 'TEACHER', 'STUDENT'], state='readonly')
        self.role_combo.grid(row=4, column=1, sticky="ew", pady=5, padx=5)

        buttons = ttk.Frame(form, style='Content.TFrame')
        buttons.grid(row=5, column=0, columnspan=2, pady=(15, 0))

        if self.is_admin:
            ttk.Button(buttons, text="Nuevo", command=self._reset, style='Primary.TButton').grid(row=0, column=0, padx=5)
            ttk.Button(buttons, text="Eliminar", command=self._delete_user, style='Danger.TButton').grid(row=0, column=2, padx=5)

        ttk.Button(buttons, text="Guardar", command=self._save_user, style='Primary.TButton').grid(row=0, column=1, padx=5)

    def _reset(self) -> None:
        self.current_user_id = None
        self.id_var.set('')
        self.email_var.set('')
        self.username_var.set('')
        self.password_var.set('')
        self.role_var.set('ADMIN' if self.is_admin else self.session.role or '')

        # Restaurar estado de campos según el rol
        state_email = 'normal' if self.is_admin else 'readonly'
        state_role = 'readonly' if self.is_admin else 'disabled'
        self.email_entry.configure(state=state_email)
        self.role_combo.configure(state=state_role)
        
        # El no-admin solo puede editar su username y password
        if not self.is_admin:
            self.username_entry.configure(state='normal')
            self.password_entry.configure(state='normal')

        if self.is_admin:
            self.tree.selection_remove(self.tree.selection())

    def _search_by_id(self) -> None:
        value = self.search_var.get().strip()
        if not value.isdigit():
            messagebox.showinfo("Buscar", "Ingresa un ID numérico válido para buscar.")
            return
        try:
            user = self.api.get(f"/users/{value}")
            self._fill_form(user)
        except ApiError as error:
            messagebox.showerror("Error de Búsqueda", error.message)
        except Exception as error: 
            messagebox.showerror("Error", str(error))

    def _on_tree_select(self, _event: tk.Event) -> None:
        if not self.is_admin: return
        
        selection = self.tree.selection()
        if not selection: return
        
        item = self.tree.item(selection[0])
        user_id = item['values'][0]
        try:
            user = self.api.get(f"/users/{user_id}")
            self._fill_form(user)
        except ApiError as error:
            messagebox.showerror("Error", error.message)
        except Exception as error: 
            messagebox.showerror("Error", str(error))

    def _fill_form(self, user: Dict[str, Any]) -> None:
        self.current_user_id = int(user.get('id'))
        self.id_var.set(str(user.get('id', '')))
        self.email_var.set(user.get('email', ''))
        self.username_var.set(user.get('username', ''))
        self.role_var.set(user.get('role', ''))
        self.password_var.set('') # Nunca mostrar la contraseña
        
        # Restaurar estado de campos
        self.email_entry.configure(state='normal' if self.is_admin else 'readonly')
        self.role_combo.configure(state='readonly' if self.is_admin else 'disabled')

    def _collect_payload(self) -> Dict[str, Any]:
        email = self.email_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get().strip() or None
        role = self.role_var.get().strip() or None

        payload: Dict[str, Any] = {}

        # --- VALIDACIONES (AÑADIDAS) ---
        if not username:
            raise ValueError('El nombre de usuario es requerido.')
        if ' ' in username:
            raise ValueError('El nombre de usuario no puede contener espacios.')

        if self.is_admin:
            if not email:
                raise ValueError('El email es requerido.')
            if not re.match(self.EMAIL_REGEX, email):
                raise ValueError('El formato del email no es válido (ej. usuario@dominio.com).')
            if not role:
                raise ValueError('El rol es requerido.')
            
            payload['email'] = email
            payload['role'] = role

        payload['username'] = username

        # Lógica de contraseña
        if self.current_user_id is None:
            # Creando nuevo usuario: contraseña es obligatoria
            if not password:
                raise ValueError('La contraseña es requerida para crear un nuevo usuario.')
            
            payload['password'] = password
        else:
            # Actualizando usuario: contraseña es opcional
            if password:
                
                payload['password'] = password
        # --- FIN VALIDACIONES ---
        
        return payload

    def _save_user(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return

        try:
            if self.current_user_id is None:
                user = self.api.post('/users', payload)
            else:
                user = self.api.put(f"/users/{self.current_user_id}", payload)
                
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return

        messagebox.showinfo("Éxito", "Usuario guardado correctamente")
        self._fill_form(user)
        if self.is_admin:
            self._load_users()

    def _delete_user(self) -> None:
        if not self.is_admin:
            messagebox.showwarning("Permiso", "Solo el administrador puede eliminar usuarios")
            return
        if self.current_user_id is None:
            messagebox.showinfo("Eliminar", "Selecciona un usuario de la tabla para eliminar.")
            return
            
        if self.current_user_id == self.session.user.get('id'):
            messagebox.showwarning("Operación Inválida", "No puedes eliminar tu propia cuenta de administrador.")
            return

        if not messagebox.askyesno("Eliminar", f"¿Deseas eliminar al usuario '{self.username_var.get()}'?"):
            return
            
        try:
            self.api.delete(f"/users/{self.current_user_id}")
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return
            
        messagebox.showinfo("Éxito", "Usuario eliminado")
        self._reset()
        if self.is_admin:
            self._load_users()

    def _load_users(self) -> None:
        if not self.is_admin: return
        try:
            users = self.api.get('/users')
        except ApiError as error:
            messagebox.showerror("Error de Carga", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return

        self.tree.delete(*self.tree.get_children())
        for user in users:
            self.tree.insert('', tk.END, values=(user['id'], user['email'], user['username'], user['role']))

    def _load_self(self) -> None:
        self.current_user_id = self.session.user.get('id')
        if not self.current_user_id:
            messagebox.showerror("Error", "No se pudo obtener tu ID de sesión.")
            return
            
        try:
            user = self.api.get(f"/users/{self.current_user_id}")
            self._fill_form(user)
            self._reset_non_admin_fields() # Asegurar estado de campos
        except ApiError as error:
            messagebox.showerror("Error", error.message)
        except Exception as error: 
            messagebox.showerror("Error", str(error))

    def _reset_non_admin_fields(self) -> None:
        # Método helper para asegurar que los no-admin no puedan editar
        if not self.is_admin:
            self.email_entry.configure(state='readonly')
            self.role_combo.configure(state='disabled')
            self.username_entry.configure(state='normal')
            self.password_entry.configure(state='normal')