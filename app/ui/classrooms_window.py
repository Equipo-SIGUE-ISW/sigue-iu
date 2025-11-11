from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession

class ClassroomsWindow(ttk.Frame):
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

        self.pack(fill=tk.BOTH, expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Gestión de Salones", font=("Segoe UI", 16, "bold"), background=self.COLOR_BG).grid(row=0, column=0, sticky="w", pady=(0, 15))

        self._build_tree(self)
        self._build_form(self)
        self._load_classrooms()

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'name', 'building')
        tree_container = ttk.Frame(container, style='Content.TFrame')
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=10)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.heading('id', text='ID'); self.tree.column('id', width=50, stretch=False)
        self.tree.heading('name', text='Nombre Salón'); self.tree.column('name', width=200)
        self.tree.heading('building', text='Edificio'); self.tree.column('building', width=200)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos del Salón", style='Form.TLabelframe', padding=15)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID", style='Content.TLabel').grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        self.name_var = tk.StringVar()
        ttk.Label(form, text="Nombre", style='Content.TLabel').grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        self.building_var = tk.StringVar()
        ttk.Label(form, text="Edificio", style='Content.TLabel').grid(row=2, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.building_var).grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        buttons = ttk.Frame(form, style='Content.TFrame')
        buttons.grid(row=3, column=0, columnspan=2, pady=15)
        
        ttk.Button(buttons, text="Nuevo", command=self._reset, style='Primary.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save, style='Primary.TButton').grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete, style='Danger.TButton').grid(row=0, column=2, padx=5)

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.building_var.set('')
        self.tree.selection_remove(self.tree.selection())

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection: return
        item = self.tree.item(selection[0]); values = item['values']
        self.current_id = int(values[0]); self.id_var.set(str(values[0]))
        self.name_var.set(values[1]); self.building_var.set(values[2])

    def _collect_payload(self) -> Dict[str, str]:
        name = self.name_var.get().strip()
        building = self.building_var.get().strip()
        
        if not name or not building:
            raise ValueError('El Nombre y el Edificio son campos requeridos.')
        
        return {'name': name, 'building': building}

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return
            
        # --- VALIDACIÓN (Nombre + Edificio) ---
        # Esta es la única validación que haremos en el frontend
        new_name_lower = payload['name'].lower()
        new_building_lower = payload['building'].lower()

        for item_id in self.tree.get_children():
            item_values = self.tree.item(item_id, 'values')
            item_db_id = int(item_values[0])
            item_name_lower = str(item_values[1]).lower()
            item_building_lower = str(item_values[2]).lower()

            if new_name_lower == item_name_lower and new_building_lower == item_building_lower:
                if self.current_id is None: # Creando nuevo
                    messagebox.showwarning("Registro Duplicado", f"Ya existe un salón '{payload['name']}' en el edificio '{payload['building']}'.")
                    return
                elif self.current_id != item_db_id: # Editando, pero coincide con OTRO registro
                    messagebox.showwarning("Registro Duplicado", f"Ya existe un salón '{payload['name']}' en el edificio '{payload['building']}'.")
                    return
        # --- FIN DE LA VALIDACIÓN ---
        
        try:
            if self.current_id is None:
                classroom = self.api.post('/classrooms', payload)
            else:
                classroom = self.api.put(f"/classrooms/{self.current_id}", payload)
                
        except ApiError as error:
            # Ahora, si la API se queja (como en tu foto), mostramos su error real.
            # No agregamos ningún texto extra.
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        
        messagebox.showinfo("Éxito", "Salón guardado correctamente")
        
        # Actualizamos el ID por si acaso era uno nuevo
        self.current_id = classroom['id']
        self.id_var.set(str(classroom['id']))
        self._load_classrooms() # Recargamos la tabla

    def _delete(self) -> None:
        if self.current_id is None:
            messagebox.showwarning("Operación", "Por favor, selecciona un salón de la tabla para eliminar.")
            return
        
        if not messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar el salón '{self.name_var.get()}' del edificio '{self.building_var.get()}'?"):
            return
        
        try:
            self.api.delete(f"/classrooms/{self.current_id}")
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        
        messagebox.showinfo("Éxito", "Salón eliminado")
        self._reset()
        self._load_classrooms()

    def _load_classrooms(self) -> None:
        try:
            classrooms = self.api.get('/classrooms')
            self.tree.delete(*self.tree.get_children())
            for classroom in classrooms:
                self.tree.insert('', tk.END, values=(classroom['id'], classroom['name'], classroom['building']))
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los salones: {e}")