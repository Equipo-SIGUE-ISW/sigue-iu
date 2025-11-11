from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional
from datetime import datetime  # <--- IMPORTADO PARA VALIDAR HORA

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession
# from app.ui.base_window import ModuleWindow # Ya no se usa

# CAMBIO 1: Heredar de ttk.Frame
class SchedulesWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, padding=20) # CAMBIO 2: Aplicar padding aquí
        self.api = api
        self.session = session
        self.current_id: Optional[int] = None

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
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Fila 1 (la tabla) se expandirá

        ttk.Label(self, text="Gestión de Horarios", font=("Segoe UI", 16, "bold"), background=self.COLOR_BG).grid(row=0, column=0, sticky="w", pady=(0, 15))

        self._build_tree(self)
        self._build_form(self)
        self._load_schedules()

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'shift', 'time')
        
        # MEJORA: Contenedor para la tabla y scrollbar
        tree_container = ttk.Frame(container, style='Content.TFrame')
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=8)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # MEJORA: Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.heading('id', text='ID')
        self.tree.column('id', width=50, stretch=False)
        self.tree.heading('shift', text='Turno')
        self.tree.column('shift', width=200)
        self.tree.heading('time', text='Hora')
        self.tree.column('time', width=150, anchor=tk.CENTER)
        
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos del horario", style='Form.TLabelframe', padding=15)
        form.grid(row=2, column=0, sticky="ew") # Fila 2
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID", style='Content.TLabel').grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        self.time_var = tk.StringVar()
        ttk.Label(form, text="Hora (HH:MM)", style='Content.TLabel').grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form, textvariable=self.time_var).grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        self.shift_var = tk.StringVar()
        ttk.Label(form, text="Turno", style='Content.TLabel').grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.shift_combo = ttk.Combobox(form, textvariable=self.shift_var, values=['MATUTINO', 'VESPERTINO'], state='readonly')
        self.shift_combo.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        buttons = ttk.Frame(form, style='Content.TFrame')
        buttons.grid(row=3, column=0, columnspan=2, pady=15)
        
        # MEJORA: Aplicar estilos a botones
        ttk.Button(buttons, text="Nuevo", command=self._reset, style='Primary.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save, style='Primary.TButton').grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete, style='Danger.TButton').grid(row=0, column=2, padx=5)

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.time_var.set('')
        self.shift_var.set('')
        self.tree.selection_remove(self.tree.selection()) # MEJORA: Deseleccionar tabla

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item['values']
        
        self.current_id = int(values[0])
        self.id_var.set(str(values[0]))
        self.shift_var.set(values[1])
        self.time_var.set(values[2])

    def _collect_payload(self) -> Dict[str, str]:
        time_value = self.time_var.get().strip()
        shift = self.shift_var.get().strip()

        # --- VALIDACIÓN ROBUSTA (AÑADIDA) ---
        if not time_value or not shift:
            raise ValueError('La hora y el turno son campos requeridos.')
        
        # Validar formato de hora HH:MM
        try:
            datetime.strptime(time_value, '%H:%M')
        except ValueError:
            raise ValueError("El formato de la hora debe ser HH:MM (ej. 07:00 o 14:30).")
        # --- FIN VALIDACIÓN ---

        return {'time': time_value, 'shift': shift}

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return
            
        try:
            if self.current_id is None:
                schedule = self.api.post('/schedules', payload)
            else:
                schedule = self.api.put(f"/schedules/{self.current_id}", payload)
                
        # --- MEJORA: Manejo de Errores ---
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return
        # ---
        
        messagebox.showinfo("Éxito", "Horario guardado")
        
        self.current_id = schedule['id']
        self.id_var.set(str(schedule['id']))
        self._load_schedules()

    def _delete(self) -> None:
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona un horario de la tabla para eliminar.")
            return
        if not messagebox.askyesno("Eliminar", f"¿Deseas eliminar el horario de las {self.time_var.get()}?"):
            return
            
        try:
            self.api.delete(f"/schedules/{self.current_id}")
            
        # --- MEJORA: Manejo de Errores ---
        except ApiError as error:
            messagebox.showerror("Error de API", error.message)
            return
        except Exception as error: 
            messagebox.showerror("Error", str(error))
            return
        # ---
        
        messagebox.showinfo("Éxito", "Horario eliminado")
        self._reset()
        self._load_schedules()

    def _load_schedules(self) -> None:
        try:
            schedules = self.api.get('/schedules')
            self.tree.delete(*self.tree.get_children())
            for schedule in schedules:
                self.tree.insert('', tk.END, values=(schedule['id'], schedule['shift'], schedule['time']))
                
        # --- MEJORA: Manejo de Errores ---
        except ApiError as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los horarios: {e.message}")
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los horarios: {e}")