from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession
# from app.ui.base_window import ModuleWindow # Ya no se usa

# CAMBIO 1: Heredar de ttk.Frame
class GroupsWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, padding=20) # CAMBIO 2: Aplicar padding aquí
        self.api = api
        self.session = session
        self.current_id: Optional[int] = None
        
        # Listas de datos para los combobox
        self.careers: List[Dict[str, Any]] = []
        self.teachers: List[Dict[str, Any]] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = []
        # MEJORA: Caché para materias, en lugar de cargar todo
        self.subjects_cache: Dict[int, List[Dict[str, Any]]] = {}

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
        self.rowconfigure(1, weight=1) # Fila 1 (tabla) se expandirá

        ttk.Label(self, text="Gestión de Grupos", font=("Segoe UI", 16, "bold"), background=self.COLOR_BG).grid(row=0, column=0, sticky="w", pady=(0, 15))

        self._build_tree(self)
        self._build_form(self)
        self._fetch_support_data()
        self._load_groups()

    def _compose_combo_value(self, data_list: List[Dict[str, Any]], kind: str, item_id: int, fallback_label: str) -> str:
        for item in data_list:
            if item.get('id') == item_id:
                if kind == 'classrooms':
                    return f"{item['id']} - {item['name']} ({item['building']})"
                if kind == 'schedules':
                    return f"{item['id']} - {item['time']} ({item['shift']})"
                label = item.get('name') or fallback_label
                return f"{item['id']} - {label}"
        return f"{item_id} - {fallback_label}"

    def _set_combo_value(self, combo: ttk.Combobox, variable: tk.StringVar, value: str) -> None:
        if not value:
            variable.set('')
            return
        values = list(combo.cget('values'))
        if value not in values:
            values.append(value)
            combo.configure(values=values)
        variable.set(value)

    def _build_tree(self, container: ttk.Frame) -> None:
        tree_container = ttk.Frame(container, style='Content.TFrame')
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        columns = ('id', 'name', 'career', 'subject', 'teacher', 'schedule')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=7)
        self.tree.grid(row=0, column=0, sticky="nsew")

        # MEJORA: Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        headers = {'id': 'ID', 'name': 'Grupo', 'career': 'Carrera', 'subject': 'Materia', 'teacher': 'Maestro', 'schedule': 'Horario'}
        col_widths = {'id': 40, 'name': 100, 'career': 150, 'subject': 150, 'teacher': 150, 'schedule': 100}

        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=col_widths[col], stretch=True)
            
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos del grupo", style='Form.TLabelframe', padding=15)
        form.grid(row=2, column=0, sticky="nsew")
        form.columnconfigure(1, weight=3) # Dar más peso a la columna de widgets
        form.columnconfigure(3, weight=3)
        form.rowconfigure(10, weight=1) # Fila de la tabla de estudiantes

        # --- Columna 0 (Izquierda) ---
        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID", style='Content.TLabel').grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        self.name_var = tk.StringVar()
        ttk.Label(form, text="Nombre de grupo", style='Content.TLabel').grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        self.career_var = tk.StringVar()
        ttk.Label(form, text="Carrera", style='Content.TLabel').grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.career_combo = ttk.Combobox(form, textvariable=self.career_var, state='readonly')
        self.career_combo.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        self.career_combo.bind('<<ComboboxSelected>>', self._refresh_subject_combo)

        self.subject_var = tk.StringVar()
        ttk.Label(form, text="Materia", style='Content.TLabel').grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.subject_combo = ttk.Combobox(form, textvariable=self.subject_var, state='readonly')
        self.subject_combo.grid(row=3, column=1, sticky="ew", pady=5, padx=5)

        # --- Columna 2 (Derecha) ---
        self.teacher_var = tk.StringVar()
        ttk.Label(form, text="Maestro", style='Content.TLabel').grid(row=0, column=2, sticky="w", pady=5, padx=5)
        self.teacher_combo = ttk.Combobox(form, textvariable=self.teacher_var, state='readonly')
        self.teacher_combo.grid(row=0, column=3, sticky="ew", pady=5, padx=5)

        self.classroom_var = tk.StringVar()
        ttk.Label(form, text="Salón", style='Content.TLabel').grid(row=1, column=2, sticky="w", pady=5, padx=5)
        self.classroom_combo = ttk.Combobox(form, textvariable=self.classroom_var, state='readonly')
        self.classroom_combo.grid(row=1, column=3, sticky="ew", pady=5, padx=5)

        self.schedule_var = tk.StringVar()
        ttk.Label(form, text="Horario", style='Content.TLabel').grid(row=2, column=2, sticky="w", pady=5, padx=5)
        self.schedule_combo = ttk.Combobox(form, textvariable=self.schedule_var, state='readonly')
        self.schedule_combo.grid(row=2, column=3, sticky="ew", pady=5, padx=5)

        self.semester_var = tk.StringVar()
        ttk.Label(form, text="Semestre", style='Content.TLabel').grid(row=3, column=2, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.semester_var).grid(row=3, column=3, sticky="ew", pady=5, padx=5)

        self.max_students_var = tk.StringVar()
        ttk.Label(form, text="Máx. alumnos", style='Content.TLabel').grid(row=4, column=2, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.max_students_var).grid(row=4, column=3, sticky="ew", pady=5, padx=5)

        # --- Botones ---
        buttons = ttk.Frame(form, style='Content.TFrame')
        buttons.grid(row=5, column=0, columnspan=4, pady=15)
        ttk.Button(buttons, text="Nuevo", command=self._reset, style='Primary.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save, style='Primary.TButton').grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete, style='Danger.TButton').grid(row=0, column=2, padx=5)

        # --- Tabla de Alumnos ---
        ttk.Label(form, text="Alumnos inscritos", style='Content.TLabel').grid(row=10, column=0, sticky="nw", pady=(15, 5), padx=5)
        
        student_tree_container = ttk.Frame(form, style='Content.TFrame')
        student_tree_container.grid(row=10, column=1, columnspan=3, sticky="nsew", pady=5, padx=5)
        student_tree_container.rowconfigure(0, weight=1)
        student_tree_container.columnconfigure(0, weight=1)

        students_columns = ('studentId', 'name', 'email', 'status')
        self.students_tree = ttk.Treeview(student_tree_container, columns=students_columns, show='headings', height=5)
        self.students_tree.grid(row=0, column=0, sticky="nsew")
        
        student_scrollbar = ttk.Scrollbar(student_tree_container, orient="vertical", command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=student_scrollbar.set)
        student_scrollbar.grid(row=0, column=1, sticky="ns")

        headers_students = {'studentId': 'ID', 'name': 'Nombre', 'email': 'Correo', 'status': 'Estado'}
        for col in students_columns:
            self.students_tree.heading(col, text=headers_students[col])
            self.students_tree.column(col, width=100, stretch=True)

    def _fetch_support_data(self) -> None:
        try:
            self.careers = self.api.get('/careers')
            self.career_combo.configure(values=[f"{item['id']} - {item['name']}" for item in self.careers])

            self.teachers = self.api.get('/teachers')
            self.teacher_combo.configure(values=[f"{item['id']} - {item['name']}" for item in self.teachers])

            self.classrooms = self.api.get('/classrooms')
            self.classroom_combo.configure(values=[f"{item['id']} - {item['name']} ({item['building']})" for item in self.classrooms])

            self.schedules = self.api.get('/schedules')
            self.schedule_combo.configure(values=[f"{item['id']} - {item['time']} ({item['shift']})" for item in self.schedules])
        except ApiError as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los datos de soporte (carreras, maestros, etc.): {e.message}")

    def _refresh_subject_combo(self, _event: Optional[tk.Event] = None) -> None:
        """Carga dinámicamente las materias de la carrera seleccionada."""
        career_id_str = self.career_var.get().split(' - ')[0]
        if not career_id_str.isdigit():
            self.subject_combo.configure(values=[])
            self.subject_var.set('')
            return
            
        career_id = int(career_id_str)
        subjects = []
        try:
            if career_id in self.subjects_cache:
                subjects = self.subjects_cache[career_id]
            else:
                subjects = self.api.get('/subjects', params={'careerId': career_id})
                self.subjects_cache[career_id] = subjects
        except ApiError as e:
            messagebox.showerror("Error de API", f"No se pudieron cargar las materias para esa carrera: {e.message}")
            
        values = [f"{item['id']} - {item['name']}" for item in subjects]
        current = self.subject_var.get()
        self.subject_combo.configure(values=values)
        
        if current not in values:
            self.subject_var.set('') # Limpiar si la materia ya no es válida

    def _load_groups(self) -> None:
        try:
            groups = self.api.get('/groups')
            self.tree.delete(*self.tree.get_children())
            for group in groups:
                self.tree.insert('', tk.END, values=(
                    group['id'],
                    group['name'],
                    group.get('careerName', 'N/A'),
                    group.get('subjectName', 'N/A'),
                    group.get('teacherName', 'N/A'),
                    f"{group.get('scheduleTime', 'N/A')}"
                ))
        except ApiError as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los grupos: {e.message}")

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection: return
        item = self.tree.item(selection[0])
        try:
            self._load_group(int(item['values'][0]))
        except ApiError as e:
            messagebox.showerror("Error", f"No se pudo cargar el grupo: {e.message}")

    def _load_group(self, group_id: int) -> None:
        # Esta función asume que _load_group(id) levanta ApiError si falla
        data = self.api.get(f'/groups/{group_id}')
        
        self.current_id = data['id']
        self.id_var.set(str(data['id']))
        self.name_var.set(data['name'])
        self.semester_var.set(str(data['semester']))
        self.max_students_var.set(str(data['maxStudents']))

        # Helper para encontrar el string correcto en la lista de combobox
        if data.get('careerId'):
            career_value = self._compose_combo_value(self.careers, 'careers', data['careerId'], data.get('careerName', 'N/A'))
            self._set_combo_value(self.career_combo, self.career_var, career_value)
        
        # Cargar materias ANTES de setear la materia
        self._refresh_subject_combo()
        if data.get('subjectId'):
            # No podemos usar find_in_list para materias, ya que se cargan dinámicamente
            subject_value = f"{data['subjectId']} - {data.get('subjectName', 'N/A')}"
            self._set_combo_value(self.subject_combo, self.subject_var, subject_value)
            
        if data.get('teacherId'):
            teacher_value = self._compose_combo_value(self.teachers, 'teachers', data['teacherId'], data.get('teacherName', 'N/A'))
            self._set_combo_value(self.teacher_combo, self.teacher_var, teacher_value)
        if data.get('classroomId'):
            classroom_value = self._compose_combo_value(self.classrooms, 'classrooms', data['classroomId'], data.get('classroomName', 'N/A'))
            self._set_combo_value(self.classroom_combo, self.classroom_var, classroom_value)
        if data.get('scheduleId'):
            schedule_value = self._compose_combo_value(self.schedules, 'schedules', data['scheduleId'], data.get('scheduleTime', 'N/A'))
            self._set_combo_value(self.schedule_combo, self.schedule_var, schedule_value)

        self._load_students(data.get('students', []))

    def _load_students(self, students: List[Dict[str, Any]]) -> None:
        self.students_tree.delete(*self.students_tree.get_children())
        for student in students:
            self.students_tree.insert('', tk.END, values=(
                student['studentId'], student['name'], student.get('email', 'N/A'), student['status']
            ))

    def _collect_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        
        # --- VALIDACIÓN ROBUSTA (AÑADIDA) ---
        name = self.name_var.get().strip()
        if not name:
            raise ValueError('El Nombre de grupo es requerido.')
        if not all(c.isalnum() or c.isspace() or c == '-' for c in name):
             raise ValueError("El nombre del grupo solo puede contener letras, números, espacios o guiones.")
        payload['name'] = name

        required_combos = [
            (self.career_var.get(), 'careerId', 'Carrera'),
            (self.subject_var.get(), 'subjectId', 'Materia'),
            (self.teacher_var.get(), 'teacherId', 'Maestro'),
            (self.classroom_var.get(), 'classroomId', 'Salón'),
            (self.schedule_var.get(), 'scheduleId', 'Horario'),
        ]
        for value, key, label in required_combos:
            if not value or not value.split(' - ')[0].isdigit():
                raise ValueError(f'Debes seleccionar una opción válida para {label}.')
            payload[key] = int(value.split(' - ')[0])

        try:
            semester = int(self.semester_var.get().strip())
            max_students = int(self.max_students_var.get().strip())
        except ValueError:
            raise ValueError('Semestre y Máx. alumnos deben ser números enteros.')

        if semester <= 0:
            raise ValueError('El semestre debe ser un número positivo (ej. 1, 2, ...).')
        if max_students <= 0:
            raise ValueError('El Máx. de alumnos debe ser un número positivo.')
        
        payload['semester'] = semester
        payload['maxStudents'] = max_students
        # --- FIN VALIDACIÓN ---

        return payload

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return
            
        try:
            if self.current_id is None:
                group = self.api.post('/groups', payload)
            else:
                group = self.api.put(f"/groups/{self.current_id}", payload)
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error:
            messagebox.showerror("Error", str(error))
            return
            
        messagebox.showinfo("Éxito", "Grupo guardado")
        self._load_group(group['id']) # Recargar el formulario
        self._load_groups() # Recargar la tabla

    def _delete(self) -> None:
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona un grupo de la tabla para eliminar.")
            return
        if not messagebox.askyesno("Eliminar", f"¿Deseas eliminar el grupo '{self.name_var.get()}'?"):
            return
            
        try:
            self.api.delete(f"/groups/{self.current_id}")
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error:
            messagebox.showerror("Error", str(error))
            return
            
        messagebox.showinfo("Éxito", "Grupo eliminado")
        self._reset()
        self._load_groups()

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.semester_var.set('')
        self.max_students_var.set('')
        self.career_var.set('')
        self.subject_var.set('')
        self.teacher_var.set('')
        self.classroom_var.set('')
        self.schedule_var.set('')
        self.students_tree.delete(*self.students_tree.get_children())
        self.tree.selection_remove(self.tree.selection()) # Deseleccionar tabla