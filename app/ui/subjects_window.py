from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

from app.services.api_client import ApiClient
from app.services.session import UserSession
from app.ui.base_window import ModuleWindow


class SubjectsWindow(ModuleWindow):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, api, session)
        self.title("Materias")
        self.current_id: Optional[int] = None
        self.careers: List[Dict[str, object]] = []

        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)

        self._build_tree(container)
        self._build_form(container)
        self._load_careers()
        self._load_subjects()

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'name', 'credits', 'semester', 'career')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', height=8)
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        container.rowconfigure(0, weight=1)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos de la materia", padding=15)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5)

        self.name_var = tk.StringVar()
        ttk.Label(form, text="Asignatura").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=5)

        self.credits_var = tk.StringVar()
        ttk.Label(form, text="Créditos").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.credits_var).grid(row=2, column=1, sticky="ew", pady=5)

        self.semester_var = tk.StringVar()
        ttk.Label(form, text="Semestre").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.semester_var).grid(row=3, column=1, sticky="ew", pady=5)

        self.career_var = tk.StringVar()
        self.careers = []
        ttk.Label(form, text="Carrera").grid(row=4, column=0, sticky="w", pady=5)
        self.career_combo = ttk.Combobox(form, textvariable=self.career_var, state='readonly')
        self.career_combo.grid(row=4, column=1, sticky="ew", pady=5)
        self.career_combo.bind('<<ComboboxSelected>>', lambda _e: self._load_subjects())

        buttons = ttk.Frame(form)
        buttons.grid(row=5, column=0, columnspan=2, pady=15)
        ttk.Button(buttons, text="Nuevo", command=self._reset).grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save).grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete).grid(row=0, column=2, padx=5)

    def _load_careers(self) -> None:
        self.careers = self.api.get('/careers')
        career_values = [f"{career['id']} - {career['name']}" for career in self.careers]
        self.career_combo.configure(values=career_values)
        if career_values and not self.career_var.get():
            self.career_var.set(career_values[0])

    def _load_subjects(self) -> None:
        self.tree.delete(*self.tree.get_children())
        print(self.careers)
        for career in self.careers:
            params = {}
            params['careerId'] = career['id']
            subjects = self.api.get('/subjects', params=params if params else None)
            for subject in subjects:
                self.tree.insert('', tk.END, values=(subject['id'], subject['name'], subject['credits'], subject['semester'], subject.get('careerName', '')))

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.credits_var.set('')
        self.semester_var.set('')

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self.current_id = int(item['values'][0])
        self.id_var.set(str(item['values'][0]))
        self.name_var.set(item['values'][1])
        self.credits_var.set(str(item['values'][2]))
        self.semester_var.set(str(item['values'][3]))
        if item['values'][4]:
            self.career_var.set(item['values'][4])

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
        except ValueError as error:
            raise ValueError('Créditos y semestre deben ser numéricos') from error
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
        try:
            if self.current_id is None:
                subject = self.api.post('/subjects', payload)
            else:
                subject = self.api.put(f"/subjects/{self.current_id}", payload)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Materia guardada")
        self.current_id = subject['id']
        self.id_var.set(str(subject['id']))
        self._load_subjects()

    def _delete(self) -> None:
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona una materia")
            return
        if not messagebox.askyesno("Eliminar", "¿Deseas eliminar la materia?"):
            return
        try:
            self.api.delete(f"/subjects/{self.current_id}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Materia eliminada")
        self._reset()
        self._load_subjects()
