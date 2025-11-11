from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession
# from app.ui.base_window import ModuleWindow # Ya no se usa

# CAMBIO 1: Heredar de ttk.Frame
class TeachersWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, padding=20)
        self.api = api
        self.session = session
        self.is_admin = session.role == 'ADMIN'
        self.current_id: Optional[int] = None
        self.user_options: Dict[str, int] = {}
        self.careers: List[Dict[str, Any]] = []
        self.subjects: List[Dict[str, Any]] = []
        self.current_subjects: List[int] = [] # Para guardar las materias seleccionadas

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
        
        # Estilo para los Listbox (fondo blanco, borde)
        self.style.configure('TListbox', background=self.COLOR_WHITE, foreground=self.COLOR_TEXT_DARK, borderwidth=1, relief='solid', fieldbackground=self.COLOR_WHITE)

        # CAMBIO 2: Layout del Frame
        self.pack(fill=tk.BOTH, expand=True)
        self.columnconfigure(0, weight=1)
        
        # Título del Módulo
        title_text = "Gestión de Maestros" if self.is_admin else "Mi Perfil de Maestro"
        ttk.Label(self, text=title_text, font=("Segoe UI", 16, "bold"), background=self.COLOR_BG).grid(row=0, column=0, sticky="w", pady=(0, 15))

        # La lógica de roles se mantiene
        if self.is_admin:
            self.rowconfigure(1, weight=1) # Fila 1 (tabla) se expande
            self._build_tree(self)
            self._build_form(self, form_row=2) # El form va en la fila 2
            self._fetch_support_data()
            self._load_teachers()
        else:
            self.rowconfigure(1, weight=1) # Permitir que el form se expanda
            self._build_form(self, form_row=1) # El form va en la fila 1
            self._fetch_support_data()
            self._load_self() # Carga solo los datos del maestro logueado


    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'name', 'email', 'degree')
        
        tree_container = ttk.Frame(container, style='Content.TFrame')
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
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
        self.tree.heading('degree', text='Grado'); self.tree.column('degree', width=100)
        
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame, form_row: int) -> None:
        form = ttk.LabelFrame(container, text="Datos del Maestro", style='Form.TLabelframe', padding=15)
        form.grid(row=form_row, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        # Fila 0: ID
        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID", style='Content.TLabel').grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        # Fila 1: Email (ComboBox para Admin, Entry para Maestro)
        ttk.Label(form, text="Email", style='Content.TLabel').grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.email_var = tk.StringVar()
        if self.is_admin:
            self.email_combo = ttk.Combobox(form, textvariable=self.email_var, state='readonly')
            self.email_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        else:
            self.email_entry = ttk.Entry(form, textvariable=self.email_var, state='readonly') # Maestro no edita su email
            self.email_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        # Fila 2: Nombre
        ttk.Label(form, text="Nombre", style='Content.TLabel').grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form, textvariable=self.name_var)
        self.name_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        # Fila 3: Grado de Estudios
        ttk.Label(form, text="Grado de estudios", style='Content.TLabel').grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.degree_var = tk.StringVar()
        self.degree_combo = ttk.Combobox(form, textvariable=self.degree_var, values=['LICENCIATURA', 'MAESTRIA', 'DOCTORADO'], state='readonly')
        self.degree_combo.grid(row=3, column=1, sticky="ew", pady=5, padx=5)

        # Fila 4: Carreras
        ttk.Label(form, text="Carreras Asignadas", style='Content.TLabel').grid(row=4, column=0, sticky="nw", pady=(15, 5), padx=5)
        # Usamos tk.Listbox porque ttk.Listbox no existe, pero le damos estilo
        self.careers_list = tk.Listbox(form, selectmode=tk.MULTIPLE, height=5, exportselection=False,
                                       bg=self.COLOR_WHITE, fg=self.COLOR_TEXT_DARK, 
                                       relief='solid', borderwidth=1, highlightthickness=0)
        self.careers_list.grid(row=4, column=1, sticky="ew", pady=(15, 5), padx=5)
        self.careers_list.bind('<<ListboxSelect>>', lambda _e: self._refresh_subject_list())

        # Fila 5: Materias
        ttk.Label(form, text="Materias que Imparte", style='Content.TLabel').grid(row=5, column=0, sticky="nw", pady=(15, 5), padx=5)
        self.subjects_list = tk.Listbox(form, selectmode=tk.MULTIPLE, height=6, exportselection=False,
                                        bg=self.COLOR_WHITE, fg=self.COLOR_TEXT_DARK, 
                                        relief='solid', borderwidth=1, highlightthickness=0)
        self.subjects_list.grid(row=5, column=1, sticky="ew", pady=(15, 5), padx=5)
        self.subjects_list.bind('<<ListboxSelect>>', lambda _e: self._update_selected_subjects())

        # Fila 6: Botones
        buttons = ttk.Frame(form, style='Content.TFrame')
        buttons.grid(row=6, column=0, columnspan=2, pady=15)
        
        if self.is_admin:
            ttk.Button(buttons, text="Nuevo", command=self._reset, style='Primary.TButton').grid(row=0, column=0, padx=5)
            ttk.Button(buttons, text="Eliminar", command=self._delete, style='Danger.TButton').grid(row=0, column=2, padx=5)
        
        ttk.Button(buttons, text="Guardar", command=self._save, style='Primary.TButton').grid(row=0, column=1, padx=5)

        # Si no es admin, deshabilitamos los campos que no puede editar
        if not self.is_admin:
            self.name_entry.config(state='disabled') # Nombre no lo edita el maestro
            self.careers_list.config(state='disabled') # Admin asigna carreras
            # El maestro SÍ puede editar su 'Grado de estudios' y 'Materias que imparte'


    def _fetch_support_data(self) -> None:
        try:
            if self.is_admin:
                users = self.api.get('/users/unassigned', params={'role': 'TEACHER', 'entity': 'teachers'})
                self.user_options = {f"{item['email']} ({item['username']})": item['id'] for item in users}
                self.email_combo.configure(values=list(self.user_options.keys()))

            self.careers = self.api.get('/careers')
            self._refresh_career_list()

            self.subjects = self.api.get('/subjects')
            self._refresh_subject_list()
        except ApiError as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los datos iniciales: {e.message}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado al cargar datos: {e}")


    def _refresh_career_list(self) -> None:
        self.careers_list.delete(0, tk.END)
        for career in self.careers:
            self.careers_list.insert(tk.END, f"{career['id']} - {career['name']}")

    def _refresh_subject_list(self) -> None:
        selected_careers = {int(self.careers_list.get(i).split(' - ')[0]) for i in self.careers_list.curselection()}
        self.subjects_list.delete(0, tk.END)
        
        for subject in self.subjects:
            # Si no hay carreras seleccionadas (modo Admin) O la materia pertenece a las carreras seleccionadas (modo Maestro)
            if not selected_careers or subject.get('careerId') in selected_careers:
                career_name = ""
                for c in self.careers: # Buscar nombre de la carrera
                    if c['id'] == subject.get('careerId'):
                        career_name = c['name']
                        break
                label = f"{subject['id']} - {subject['name']} ({career_name})"
                self.subjects_list.insert(tk.END, label)
        
        # Restaurar selección previa
        for index in range(self.subjects_list.size()):
            subject_id = int(self.subjects_list.get(index).split(' - ')[0])
            if hasattr(self, 'current_subjects') and subject_id in getattr(self, 'current_subjects'):
                self.subjects_list.selection_set(index)
        self._update_selected_subjects()

    def _load_teachers(self) -> None:
        try:
            teachers = self.api.get('/teachers')
            self.tree.delete(*self.tree.get_children())
            for teacher in teachers:
                self.tree.insert('', tk.END, values=(teacher['id'], teacher['name'], teacher['email'], teacher.get('degree', 'N/A')))
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los maestros: {e}")

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection: return
        item = self.tree.item(selection[0])
        self._load_teacher(int(item['values'][0]))

    def _load_teacher(self, teacher_id: int) -> None:
        try:
            data = self.api.get(f'/teachers/{teacher_id}')
        except ApiError as e:
            messagebox.showerror("Error", f"No se pudo cargar el maestro: {e.message}")
            return
            
        self.current_id = teacher_id
        self.id_var.set(str(data['id']))
        self.name_var.set(data['name'])
        self.degree_var.set(data.get('degree', '')) 
        
        self.current_subjects = [subject['subjectId'] for subject in data.get('subjects', [])]

        if self.is_admin:
            label = next((key for key, value in self.user_options.items() if value == data.get('userId')), data.get('email', ''))
            if label not in self.user_options and data.get('userId'):
                self.user_options[label] = data.get('userId')
                self.email_combo.configure(values=list(self.user_options.keys()))
            self.email_var.set(label)
        else:
            self.email_var.set(data.get('email', ''))

        career_ids = [career['careerId'] for career in data.get('careers', [])]
        self.careers_list.selection_clear(0, tk.END)
        for index in range(self.careers_list.size()):
            career_id_in_list = int(self.careers_list.get(index).split(' - ')[0])
            if career_id_in_list in career_ids:
                self.careers_list.selection_set(index)
        
        self._refresh_subject_list()

    def _update_selected_subjects(self) -> None:
        self.current_subjects = [
            int(self.subjects_list.get(i).split(' - ')[0]) for i in self.subjects_list.curselection()
        ]

    def _load_self(self) -> None:
        try:
            data = self.api.get('/teachers/me')
            self._load_teacher(data['id'])
        except ApiError as e:
            messagebox.showerror("Error", f"No se pudo cargar tu perfil: {e.message}")
        except Exception as error: 
            messagebox.showerror("Error", str(error))

    def _collect_payload(self) -> Dict[str, Any]:
        # Obtenemos los datos de la UI
        name = self.name_var.get().strip()
        degree = self.degree_var.get().strip() or None

        # --- VALIDACIÓN DE NOMBRE (AÑADIDA) ---
        if not name:
            raise ValueError('El nombre es requerido.')
        
        for char in name:
            # Si el carácter NO es una letra Y NO es un espacio...
            if not (char.isalpha() or char.isspace()):
                # Lanzar un error
                raise ValueError(f"El nombre solo puede contener letras y espacios. El carácter '{char}' no es válido.")
        # --- FIN VALIDACIÓN ---

        payload: Dict[str, Any] = {
            'name': name,
            'degree': degree or None
        }

        # Comprobación del grado (ahora solo para 'degree')
        if not payload['degree']:
            raise ValueError('El grado de estudios es requerido.')

        # --- El resto de la función sigue igual ---

        if self.is_admin:
            email_label = self.email_var.get()
            user_id = self.user_options.get(email_label)
            
            if self.current_id is None and not user_id:
                raise ValueError('Al crear un nuevo maestro, debes seleccionar un correo de usuario disponible.')
            if user_id:
                payload['userId'] = user_id

            career_ids = [int(self.careers_list.get(i).split(' - ')[0]) for i in self.careers_list.curselection()]
            payload['careerIds'] = career_ids
            
        # Para todos (Admin y Maestro), las materias seleccionadas son las que se guardan
        subject_ids = [int(self.subjects_list.get(i).split(' - ')[0]) for i in self.subjects_list.curselection()]
        payload['subjectIds'] = subject_ids

        return payload

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return

        try:
            if self.current_id is None:
                response = self.api.post('/teachers', payload)
            else:
                response = self.api.put(f"/teachers/{self.current_id}", payload)
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return

        messagebox.showinfo("Éxito", "Maestro guardado")
        
        if self.is_admin:
            self._fetch_support_data() # Recarga usuarios no asignados
            self._load_teacher(response['id']) # Recarga el formulario
            self._load_teachers() # Recarga la tabla
        else:
            self._load_teacher(response['id']) # Recarga su propio perfil

    def _delete(self) -> None:
        if not self.is_admin:
            messagebox.showwarning("Permiso", "Solo el administrador puede eliminar maestros")
            return
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona un maestro de la tabla para eliminar.")
            return
        if not messagebox.askyesno("Eliminar", "¿Deseas eliminar el maestro?"):
            return
        
        try:
            self.api.delete(f"/teachers/{self.current_id}")
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return
        
        messagebox.showinfo("Éxito", "Maestro eliminado")
        self._reset()
        if self.is_admin:
            self._fetch_support_data()
            self._load_teachers()

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.degree_var.set('')
        self.email_var.set('')
        self.careers_list.selection_clear(0, tk.END)
        self.subjects_list.selection_clear(0, tk.END)
        self.current_subjects = []
        if self.is_admin:
            self.tree.selection_remove(self.tree.selection())
            self._fetch_support_data() # Recargar usuarios por si se cancela una creación