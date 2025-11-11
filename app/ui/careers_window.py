from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession
# Ya no es una ventana emergente
# from app.ui.base_window import ModuleWindow 


# Hereda de ttk.Frame
class CareersWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, padding=20)
        self.api = api
        self.session = session
        self.current_id: Optional[int] = None

        # --- Paleta de Colores ---
        self.COLOR_BG = "#ecf0f1"
        self.COLOR_PRIMARY = "#3498db"
        self.COLOR_DANGER = "#e74c3c"
        self.COLOR_TEXT_DARK = "#2c3e50"
        self.COLOR_WHITE = "#ffffff"
        self.COLOR_GRAY_BORDER = "#bdc3c7"

        # --- Estilos ---
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

        # Layout del Frame
        self.pack(fill=tk.BOTH, expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Fila 1 (la tabla) se expandirá

        ttk.Label(self, text="Gestión de Carreras", font=("Segoe UI", 16, "bold"), background=self.COLOR_BG).grid(row=0, column=0, sticky="w", pady=(0, 15))

        self._build_tree(self)
        self._build_form(self)
        self._load_careers()

    def _build_tree(self, container: ttk.Frame) -> None:
        # --- RE-AGREGADO "semesters" ---
        columns = ('id', 'name', 'semesters')
        
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
        self.tree.heading('name', text='Nombre Carrera')
        self.tree.column('name', width=400)
        # --- RE-AGREGADO "semesters" ---
        self.tree.heading('semesters', text='Semestres')
        self.tree.column('semesters', width=100, anchor=tk.CENTER)
        
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos de la Carrera", style='Form.TLabelframe', padding=15)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID", style='Content.TLabel').grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        self.name_var = tk.StringVar()
        ttk.Label(form, text="Nombre", style='Content.TLabel').grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        # --- RE-AGREGADO "semesters" ---
        self.semesters_var = tk.StringVar()
        ttk.Label(form, text="Número de semestres", style='Content.TLabel').grid(row=2, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.semesters_var).grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        buttons = ttk.Frame(form, style='Content.TFrame')
        buttons.grid(row=3, column=0, columnspan=2, pady=15)
        
        ttk.Button(buttons, text="Nuevo", command=self._reset, style='Primary.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save, style='Primary.TButton').grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete, style='Danger.TButton').grid(row=0, column=2, padx=5)

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.semesters_var.set('') # --- RE-AGREGADO ---
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
        self.semesters_var.set(str(values[2])) # --- RE-AGREGADO ---

    def _collect_payload(self) -> Dict[str, object]:
        name = self.name_var.get().strip()
        semesters = self.semesters_var.get().strip() # --- RE-AGREGADO ---
        
        if not name or not semesters: # --- RE-AGREGADO ---
            raise ValueError('Todos los campos son requeridos')
        
        try:
            semesters_int = int(semesters) # --- RE-AGREGADO ---
            if semesters_int <= 0:
                raise ValueError() # Forzar el error de abajo
        except ValueError as error:
            raise ValueError('El número de semestres debe ser un número entero positivo') from error
        
        return {'name': name, 'semesters': semesters_int} # --- RE-AGREGADO ---

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return
        
        # Validación de duplicado (Frontend)
        new_name_lower = payload['name'].lower()
        for item_id in self.tree.get_children():
            item_values = self.tree.item(item_id, 'values')
            item_db_id = int(item_values[0])
            item_name_lower = str(item_values[1]).lower()
            if new_name_lower == item_name_lower:
                if self.current_id is None or self.current_id != item_db_id:
                    messagebox.showwarning("Registro Duplicado", f"Ya existe una carrera con el nombre '{payload['name']}'.")
                    return
        
        try:
            if self.current_id is None:
                career = self.api.post('/careers', payload)
            else:
                career = self.api.put(f"/careers/{self.current_id}", payload)
                
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        
        messagebox.showinfo("Éxito", "Carrera guardada correctamente")
        
        self.current_id = career['id']
        self.id_var.set(str(career['id']))
        self._load_careers()

    def _delete(self) -> None:
        if self.current_id is None:
            messagebox.showwarning("Operación", "Por favor, selecciona una carrera de la tabla para eliminar.")
            return
        
        if not messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar la carrera '{self.name_var.get()}'?"):
            return
        
        try:
            self.api.delete(f"/careers/{self.current_id}")
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        
        messagebox.showinfo("Éxito", "Carrera eliminada")
        self._reset()
        self._load_careers()

    def _load_careers(self) -> None:
        try:
            careers = self.api.get('/careers')
            self.tree.delete(*self.tree.get_children())
            for career in careers:
                # --- RE-AGREGADO "semesters" ---
                self.tree.insert('', tk.END, values=(career['id'], career['name'], career['semesters']))
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar las carreras: {e}")