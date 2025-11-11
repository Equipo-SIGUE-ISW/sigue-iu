from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional
from datetime import datetime  # <--- IMPORTADO PARA VALIDAR FECHA

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession
# from app.ui.base_window import ModuleWindow # Ya no se usa

# CAMBIO 1: Heredar de ttk.Frame
class StudentsWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, padding=20) # CAMBIO 2: Aplicar padding aquí
        self.api = api
        self.session = session
        self.is_admin = session.role == 'ADMIN'
        self.is_student = session.role == 'STUDENT'
        self.current_id: Optional[int] = None
        self.user_options: Dict[str, int] = {}
        self.careers: List[Dict[str, Any]] = []
        self.subjects_cache: Dict[int, List[Dict[str, Any]]] = {}
        self.current_subjects: List[int] = []

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
        self.style.configure('TListbox', background=self.COLOR_WHITE, foreground=self.COLOR_TEXT_DARK, borderwidth=1, relief='solid', fieldbackground=self.COLOR_WHITE)

        # CAMBIO 3: Layout directo en el frame
        self.pack(fill=tk.BOTH, expand=True)
        self.columnconfigure(0, weight=1)
        
        # Título del Módulo
        title_text = "Gestión de Alumnos" if self.is_admin else "Mi Perfil de Alumno"
        ttk.Label(self, text=title_text, font=("Segoe UI", 16, "bold"), background=self.COLOR_BG).grid(row=0, column=0, sticky="w", pady=(0, 15))

        # CAMBIO 4: Lógica de UI por Rol
        if self.is_admin:
            self.rowconfigure(2, weight=1) # Fila 2 (la tabla) se expandirá
            self._build_search(self)
            self._build_tree(self)
            self._build_form(self, form_row=3) # El form va en la fila 3
        else:
            self.rowconfigure(1, weight=1) # Permitir que el form se expanda
            self._build_form(self, form_row=1) # El form va en la fila 1

        self._fetch_initial_data()

        if self.is_admin:
            self._load_students()
        else:
            self._load_self()

    def _build_search(self, container: ttk.Frame) -> None:
        search_frame = ttk.Frame(container, style='Content.TFrame')
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(search_frame, text="Buscar por ID:", style='Content.TLabel').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Buscar", command=self._search, style='Primary.TButton').pack(side=tk.LEFT)

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'name', 'email', 'status', 'career')
        
        tree_container = ttk.Frame(container, style='Content.TFrame')
        tree_container.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=7)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.heading('id', text='ID'); self.tree.column('id', width=40, stretch=False)
        self.tree.heading('name', text='Nombre'); self.tree.column('name', width=250)
        self.tree.heading('email', text='Email'); self.tree.column('email', width=250)
        self.tree.heading('status', text='Estado'); self.tree.column('status', width=80, anchor=tk.CENTER)
        self.tree.heading('career', text='Carrera'); self.tree.column('career', width=200)

        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame, form_row: int) -> None:
        form = ttk.LabelFrame(container, text="Datos del alumno", style='Form.TLabelframe', padding=15)
        form.grid(row=form_row, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID", style='Content.TLabel').grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.id_entry = ttk.Entry(form, textvariable=self.id_var, state='readonly')
        self.id_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        ttk.Label(form, text="Email", style='Content.TLabel').grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.email_var = tk.StringVar()
        self.email_combo = ttk.Combobox(form, textvariable=self.email_var, state='readonly')
        self.email_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        ttk.Label(form, text="Nombre", style='Content.TLabel').grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form, textvariable=self.name_var)
        self.name_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        ttk.Label(form, text="Estado", style='Content.TLabel').grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(form, textvariable=self.status_var, values=['ACTIVE', 'INACTIVE'], state='readonly')
        self.status_combo.grid(row=3, column=1, sticky="ew", pady=5, padx=5)

        ttk.Label(form, text="Fecha nacimiento (YYYY-MM-DD)", style='Content.TLabel').grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.birth_var = tk.StringVar()
        self.birth_entry = ttk.Entry(form, textvariable=self.birth_var)
        self.birth_entry.grid(row=4, column=1, sticky="ew", pady=5, padx=5)

        ttk.Label(form, text="Carrera", style='Content.TLabel').grid(row=5, column=0, sticky="w", pady=5, padx=5)
        self.career_var = tk.StringVar()
        self.career_combo = ttk.Combobox(form, textvariable=self.career_var, state='readonly')
        self.career_combo.grid(row=5, column=1, sticky="ew", pady=5, padx=5)
        self.career_combo.bind('<<ComboboxSelected>>', lambda _e: self._load_subjects())

        ttk.Label(form, text="Materias (Inscripción)", style='Content.TLabel').grid(row=6, column=0, sticky="nw", pady=(15, 5), padx=5)
        self.subjects_list = tk.Listbox(form, selectmode=tk.MULTIPLE, height=6, exportselection=False,
                                        bg=self.COLOR_WHITE, fg=self.COLOR_TEXT_DARK, 
                                        relief='solid', borderwidth=1, highlightthickness=0)
        self.subjects_list.grid(row=6, column=1, sticky="ew", pady=(15, 5), padx=5)

        buttons = ttk.Frame(form, style='Content.TFrame')
        buttons.grid(row=7, column=0, columnspan=2, pady=15)
        
        if self.is_admin:
            ttk.Button(buttons, text="Nuevo", command=self._reset, style='Primary.TButton').grid(row=0, column=0, padx=5)
            ttk.Button(buttons, text="Eliminar", command=self._delete, style='Danger.TButton').grid(row=0, column=2, padx=5)

        ttk.Button(buttons, text="Guardar", command=self._save, style='Primary.TButton').grid(row=0, column=1, padx=5)

    def _fetch_initial_data(self) -> None:
        try:
            if self.is_admin:
                users = self.api.get('/users/unassigned', params={'role': 'STUDENT', 'entity': 'students'})
                self.user_options = {f"{item['email']} ({item['username']})": item['id'] for item in users}
                self.email_combo.configure(values=list(self.user_options.keys()))
            else:
                self.email_combo.configure(state='disabled')

            self.careers = self.api.get('/careers')
            career_values = [f"{career['id']} - {career['name']}" for career in self.careers]
            self.career_combo.configure(values=career_values)
            
            if not self.is_admin:
                self.career_combo.configure(state='disabled')
                self.name_entry.configure(state='disabled')
                self.status_combo.configure(state='disabled')
                self.birth_entry.configure(state='disabled')
        except ApiError as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los datos iniciales: {e.message}")

    def _load_subjects(self, career_id: Optional[int] = None) -> None:
        if career_id is None:
            selected = self.career_var.get().split(' - ')[0]
            if not selected:
                return
            career_id = int(selected)
        
        try:
            if career_id in self.subjects_cache:
                subjects = self.subjects_cache[career_id]
            else:
                subjects = self.api.get('/subjects', params={'careerId': career_id})
                self.subjects_cache[career_id] = subjects

            self.subjects_list.delete(0, tk.END)
            for subject in subjects:
                self.subjects_list.insert(tk.END, f"{subject['id']} - {subject['name']}")

            # Restaurar selección
            for index, subject in enumerate(subjects):
                if subject['id'] in self.current_subjects:
                    self.subjects_list.selection_set(index)
        except ApiError as e:
            messagebox.showerror("Error de API", f"No se pudieron cargar las materias: {e.message}")

    def _search(self) -> None:
        value = self.search_var.get().strip()
        if not value.isdigit():
            messagebox.showinfo("Buscar", "Ingresa un ID numérico válido.")
            return
        try:
            self._load_student(int(value))
        except ApiError as e:
            messagebox.showerror("Error de Búsqueda", e.message)

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection: return
        item = self.tree.item(selection[0])
        self._load_student(int(item['values'][0]))

    def _load_students(self) -> None:
        try:
            # --- INICIO DE LA MEJORA ---
            # 1. Asegurarnos de tener el mapa de carreras
            #    (Normalmente _fetch_initial_data ya lo cargó, pero esto es más seguro)
            if not self.careers:
                self.careers = self.api.get('/careers')
                
            # 2. Crear un "mapa" para buscar nombres de carrera por ID
            #    Ej: {1: "Ingeniería en Computación", 2: "Derecho"}
            career_map = {career['id']: career['name'] for career in self.careers}
            # --- FIN DE LA MEJORA ---

            students = self.api.get('/students')
            tree = getattr(self, 'tree', None)
            if not tree: return
            
            tree.delete(*tree.get_children())
            for student in students:
                # --- APLICACIÓN DE LA MEJORA ---
                # 3. Buscar el nombre de la carrera usando el mapa
                career_id = student.get('careerId') # Asumimos que la API SÍ envía 'careerId'
                career_name = career_map.get(career_id, 'N/A') # Buscar, si no, 'N/A'
                
                tree.insert('', tk.END, values=(
                    student['id'], student['name'], student['email'], 
                    student['status'], career_name # 4. Usar el nombre encontrado
                ))
        except ApiError as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los alumnos: {e.message}")
        except Exception as e:
             messagebox.showerror("Error", f"Ocurrió un error al cargar alumnos: {e}")

    def _load_student(self, student_id: int) -> None:
        try:
            data = self.api.get(f'/students/{student_id}')
        except ApiError as e:
            messagebox.showerror("Error", f"No se pudo cargar el alumno: {e.message}")
            return

        self.current_id = student_id
        self.id_var.set(str(data['id']))
        self.name_var.set(data['name'])
        self.status_var.set(data['status'])
        self.birth_var.set(data.get('dateOfBirth', '')) # Usar .get() por si es nulo
        self.current_subjects = [subject['subjectId'] for subject in data.get('subjects', [])]

        if self.is_admin:
            label = next((key for key, value in self.user_options.items() if value == data['userId']), data['email'])
            if label not in self.user_options and data.get('userId'):
                self.user_options[label] = data['userId']
                self.email_combo.configure(values=list(self.user_options.keys()))
            self.email_var.set(label)
        else:
            self.email_var.set(data['email'])

        if data.get('careerId'):
            career_str = ""
            for career in self.careers:
                if career['id'] == data['careerId']:
                    career_str = f"{career['id']} - {career['name']}"
                    break
            self.career_var.set(career_str)
            self._load_subjects(data['careerId'])
        else:
            self.career_var.set("")
            self.subjects_list.delete(0, tk.END)

    def _load_self(self) -> None:
        try:
            data = self.api.get('/students/me')
            self._load_student(data['id'])
        except ApiError as e:
            messagebox.showerror("Error", f"No se pudo cargar tu perfil: {e.message}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.status_var.set('')
        self.birth_var.set('')
        self.career_var.set('')
        self.email_var.set('')
        self.subjects_list.delete(0, tk.END)
        self.current_subjects = []
        if self.is_admin:
            self.tree.selection_remove(self.tree.selection())
            self._fetch_initial_data() # Recargar usuarios no asignados

    def _collect_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}

        selected_subjects = [self.subjects_list.get(i) for i in self.subjects_list.curselection()]
        subjects_ids = [int(text.split(' - ')[0]) for text in selected_subjects]
        payload['subjects'] = subjects_ids

        if self.is_admin:
            email_label = self.email_var.get()
            user_id = self.user_options.get(email_label)
            if self.current_id is None and not user_id: # Solo requerido al crear
                raise ValueError('Debes seleccionar un correo de usuario disponible para crear un alumno.')
            if user_id:
                payload['userId'] = user_id

            name = self.name_var.get().strip()
            status = self.status_var.get().strip()
            dob = self.birth_var.get().strip()
            career_value = self.career_var.get().strip()

            if not name or not status or not dob or not career_value:
                raise ValueError('Los campos Nombre, Estado, Fecha de Nacimiento y Carrera son requeridos.')

            # --- VALIDACIÓN DE NOMBRE (AÑADIDA) ---
            for char in name:
                if not (char.isalpha() or char.isspace()):
                    raise ValueError(f"El nombre solo puede contener letras y espacios. Carácter no válido: '{char}'")
            
            # --- VALIDACIÓN DE FECHA (AÑADIDA) ---
            try:
                datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                raise ValueError("La fecha de nacimiento debe estar en formato YYYY-MM-DD (ej. 1995-01-30).")

            payload['name'] = name
            payload['status'] = status
            payload['dateOfBirth'] = dob
            payload['careerId'] = int(career_value.split(' - ')[0])
        else:
            if self.current_id is None:
                raise ValueError('No hay ningún alumno cargado para guardar.')

        return payload

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return

        try:
            if self.current_id is None:
                response = self.api.post('/students', payload)
            else:
                response = self.api.put(f"/students/{self.current_id}", payload)
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return

        messagebox.showinfo("Éxito", "Alumno guardado")
        
        # Recargar datos
        if self.is_admin:
            self._fetch_initial_data() # Recargar usuarios
        
        self._load_student(response['id']) # Recargar formulario
        
        if self.is_admin:
            self._load_students() # Recargar tabla

    def _delete(self) -> None:
        if not self.is_admin:
            messagebox.showwarning("Permiso", "Solo el administrador puede eliminar alumnos")
            return
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona un alumno de la tabla para eliminar.")
            return
        if not messagebox.askyesno("Eliminar", f"¿Deseas eliminar al alumno '{self.name_var.get()}'?"):
            return
            
        try:
            self.api.delete(f"/students/{self.current_id}")
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return
            
        messagebox.showinfo("Éxito", "Alumno eliminado")
        self._reset()
        if self.is_admin:
            self._fetch_initial_data()
            self._load_students()