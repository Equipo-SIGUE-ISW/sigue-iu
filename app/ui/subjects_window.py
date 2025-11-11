from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession
# Ya no es una ventana emergente
# from app.ui.base_window import ModuleWindow


# CAMBIO 1: Heredar de ttk.Frame
class SubjectsWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, padding=20)
        self.api = api
        self.session = session
        self.current_id: Optional[int] = None
        self.careers: List[Dict[str, object]] = []

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

        # CAMBIO 2: Layout del Frame
        self.pack(fill=tk.BOTH, expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Fila 1 (la tabla) se expandirá

        ttk.Label(self, text="Gestión de Materias", font=("Segoe UI", 16, "bold"), background=self.COLOR_BG).grid(row=0, column=0, sticky="w", pady=(0, 15))

        self._build_tree(self)
        self._build_form(self)
        
        # Cargar datos
        self._load_careers()
        # _load_subjects() se llamará automáticamente después de cargar las carreras

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'name', 'credits', 'semester', 'career')
        
        tree_container = ttk.Frame(container, style='Content.TFrame')
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=10)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.heading('id', text='ID')
        self.tree.column('id', width=50, stretch=False)
        self.tree.heading('name', text='Asignatura')
        self.tree.column('name', width=300)
        self.tree.heading('credits', text='Créditos')
        self.tree.column('credits', width=80, anchor=tk.CENTER)
        self.tree.heading('semester', text='Semestre')
        self.tree.column('semester', width=80, anchor=tk.CENTER)
        self.tree.heading('career', text='Carrera')
        self.tree.column('career', width=200)
        
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos de la Materia", style='Form.TLabelframe', padding=15)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        # --- Fila 0: ID ---
        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID", style='Content.TLabel').grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        # --- Fila 1: Asignatura ---
        self.name_var = tk.StringVar()
        ttk.Label(form, text="Asignatura", style='Content.TLabel').grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        # --- Fila 2: Créditos y Semestre ---
        credits_frame = ttk.Frame(form, style='Content.TFrame')
        credits_frame.grid(row=2, column=1, sticky="ew")
        
        self.credits_var = tk.StringVar()
        ttk.Label(form, text="Créditos", style='Content.TLabel').grid(row=2, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(credits_frame, textvariable=self.credits_var, width=10).pack(side=tk.LEFT, padx=(5, 20))

        self.semester_var = tk.StringVar()
        ttk.Label(credits_frame, text="Semestre", style='Content.TLabel').pack(side=tk.LEFT, padx=5)
        ttk.Entry(credits_frame, textvariable=self.semester_var, width=10).pack(side=tk.LEFT, padx=5)

        # --- Fila 3: Carrera ---
        self.career_var = tk.StringVar()
        self.careers = []
        ttk.Label(form, text="Carrera", style='Content.TLabel').grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.career_combo = ttk.Combobox(form, textvariable=self.career_var, state='readonly')
        self.career_combo.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        
        # --- CORRECCIÓN DE LÓGICA ---
        # Al seleccionar una carrera, se recargan las materias
        self.career_combo.bind('<<ComboboxSelected>>', self._load_subjects)

        # --- Fila 4: Botones ---
        buttons = ttk.Frame(form, style='Content.TFrame')
        buttons.grid(row=4, column=0, columnspan=2, pady=15)
        
        ttk.Button(buttons, text="Nuevo", command=self._reset, style='Primary.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save, style='Primary.TButton').grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete, style='Danger.TButton').grid(row=0, column=2, padx=5)

    def _load_careers(self) -> None:
        try:
            self.careers = self.api.get('/careers')
            career_values = [f"{c['id']} - {c['name']}" for c in self.careers]
            self.career_combo.configure(values=career_values)
            if career_values:
                self.career_var.set(career_values[0])
                # Cargar materias de la primera carrera en la lista
                self._load_subjects()
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar las carreras: {e}")

    # --- FUNCIÓN LÓGICA CORREGIDA ---
    def _load_subjects(self, _event: Optional[tk.Event] = None) -> None:
        """Carga las materias (en la tabla) filtrando por la carrera seleccionada en el combobox."""
        self.tree.delete(*self.tree.get_children()) # Limpiar tabla
        
        selected_career_str = self.career_var.get()
        if not selected_career_str:
            return # No hay carrera seleccionada

        try:
            career_id = int(selected_career_str.split(' - ')[0])
            params = {'careerId': career_id}
            subjects = self.api.get('/subjects', params=params)
            
            # Obtener el nombre de la carrera del string (para no hacer otra llamada API)
            career_name = " ".join(selected_career_str.split(' - ')[1:])

            for subject in subjects:
                self.tree.insert('', tk.END, values=(
                    subject['id'], subject['name'], subject['credits'], 
                    subject['semester'], career_name # Usar el nombre de la carrera ya conocido
                ))
        except ApiError as e:
            messagebox.showerror("Error de API", f"No se pudieron cargar las materias: {e.message}")
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar las materias: {e}")

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.credits_var.set('')
        self.semester_var.set('')
        # No reseteamos la carrera, para mantener el filtro
        self.tree.selection_remove(self.tree.selection())

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item['values']
        
        self.current_id = int(values[0])
        self.id_var.set(str(values[0]))
        self.name_var.set(values[1])
        self.credits_var.set(str(values[2]))
        self.semester_var.set(str(values[3]))
        
        # --- LÓGICA CORREGIDA ---
        # Buscar la carrera en nuestra lista `self.careers` para setear el string "ID - Nombre"
        career_name = values[4]
        for career in self.careers:
            if career['name'] == career_name:
                self.career_var.set(f"{career['id']} - {career['name']}")
                break

    def _collect_payload(self) -> Dict[str, object]:
        name = self.name_var.get().strip()
        credits = self.credits_var.get().strip()
        semester = self.semester_var.get().strip()
        career = self.career_var.get().strip()
        
        if not name or not credits or not semester or not career:
            raise ValueError('Todos los campos son requeridos')
        
        try:
            credits_int = int(credits)
            semester_int = int(semester)
            # --- VALIDACIÓN SUGERIDA ---
            if credits_int <= 0 or semester_int <= 0:
                raise ValueError("Créditos y semestre deben ser números positivos")
        except ValueError:
            raise ValueError('Créditos y semestre deben ser números enteros positivos')
        
        return {
            'name': name,
            'credits': credits_int,
            'semester': semester_int,
            'careerId': int(career.split(' - ')[0])
        }

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return
        
        # Validación de duplicado (Frontend)
        new_name_lower = payload['name'].lower()
        new_career_id = payload['careerId']

        for item_id in self.tree.get_children():
            item_values = self.tree.item(item_id, 'values')
            item_db_id = int(item_values[0])
            item_name_lower = str(item_values[1]).lower()
            
            # Buscamos el ID de la carrera del item en la tabla
            item_career_id = None
            for c in self.careers:
                if c['name'] == str(item_values[4]):
                    item_career_id = c['id']
                    break
            
            if new_name_lower == item_name_lower and new_career_id == item_career_id:
                if self.current_id is None or self.current_id != item_db_id:
                    messagebox.showwarning("Registro Duplicado", f"Ya existe una materia con ese nombre en esa carrera.")
                    return

        try:
            if self.current_id is None:
                subject = self.api.post('/subjects', payload)
            else:
                subject = self.api.put(f"/subjects/{self.current_id}", payload)
                
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        
        messagebox.showinfo("Éxito", "Materia guardada correctamente")
        
        self.current_id = subject['id']
        self.id_var.set(str(subject['id']))
        self._load_subjects() # Recargar la tabla

    def _delete(self) -> None:
        if self.current_id is None:
            messagebox.showwarning("Operación", "Por favor, selecciona una materia de la tabla para eliminar.")
            return
        
        if not messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar la materia '{self.name_var.get()}'?"):
            return
        
        try:
            self.api.delete(f"/subjects/{self.current_id}")
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        
        messagebox.showinfo("Éxito", "Materia eliminada")
        self._reset()
        self._load_subjects()