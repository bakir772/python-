#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, simpledialog, ttk

APP_NAME = "مهماتك"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mohammatak.db")
FONT = ("Tahoma", 11)
FONT_BOLD = ("Tahoma", 12, "bold")

PRIORITIES = {
    1: ("عاجل", "#d93025"),
    2: ("مهم", "#f29900"),
    3: ("عادي", "#1a73e8"),
    4: ("منخفض", "#5f6368"),
}
PRIORITY_BY_NAME = {name: num for num, (name, _) in PRIORITIES.items()}

VIEWS = [
    ("today", "اليوم"),
    ("upcoming", "القادمة"),
    ("all", "كل المهام"),
    ("done", "المكتملة"),
]


class Database:

    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                notes TEXT DEFAULT '',
                project_id INTEGER NOT NULL DEFAULT 1,
                priority INTEGER NOT NULL DEFAULT 4,
                due_date TEXT,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)
        if (
            self.conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            == 0
        ):
            self.conn.execute(
                "INSERT INTO projects (id, name) VALUES (1, 'الوارد')"
            )
            self.conn.commit()

    def get_projects(self):
        return self.conn.execute(
            "SELECT * FROM projects ORDER BY id"
        ).fetchall()

    def add_project(self, name):
        self.conn.execute("INSERT INTO projects (name) VALUES (?)", (name,))
        self.conn.commit()

    def delete_project(self, project_id):
        if project_id == 1:
            return
        self.conn.execute(
            "UPDATE tasks SET project_id=1 WHERE project_id=?", (project_id,)
        )
        self.conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        self.conn.commit()

    def get_tasks(self, view="all", project_id=None, search=""):
        today = date.today().isoformat()
        sql = (
            "SELECT t.*, p.name AS project_name FROM tasks t "
            "JOIN projects p ON p.id = t.project_id WHERE 1=1"
        )
        params = []

        if project_id:
            sql += " AND t.project_id=?"
            params.append(project_id)
        elif view == "today":
            sql += " AND t.done = 0 AND t.due_date <= ?"
            params.append(today)
        elif view == "upcoming":
            sql += " AND t.done = 0 AND t.due_date > ?"
            params.append(today)
        elif view == "done":
            sql += " AND t.done = 1"
        else:
            sql += " AND t.done = 0"

        if search:
            sql += " AND (t.title LIKE ? OR t.notes LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]

        sql += " ORDER BY t.priority, t.due_date IS NULL, t.due_date, t.id DESC"
        return self.conn.execute(sql, params).fetchall()

    def get_task(self, task_id):
        return self.conn.execute(
            "SELECT * FROM tasks WHERE id=?", (task_id,)
        ).fetchone()

    def counts(self):
        today = date.today().isoformat()
        q = lambda sql, *a: self.conn.execute(sql, a).fetchone()[0]
        return {
            "today": q(
                "SELECT COUNT(*) FROM tasks WHERE done = 0 AND due_date <= ?",
                today,
            ),
            "upcoming": q(
                "SELECT COUNT(*) FROM tasks WHERE done = 0 AND due_date > ?",
                today,
            ),
            "all": q("SELECT COUNT(*) FROM tasks WHERE done = 0"),
            "done": q("SELECT COUNT(*) FROM tasks WHERE done = 1"),
        }

    def add_task(self, title, notes, project_id, priority, due_date):
        self.conn.execute(
            "INSERT INTO tasks (title, notes, project_id, priority, due_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, notes, project_id, priority, due_date),
        )
        self.conn.commit()

    def update_task(
        self, task_id, title, notes, project_id, priority, due_date
    ):
        self.conn.execute(
            "UPDATE tasks SET title=?, notes=?, project_id=?, priority=?, due_date=? "
            "WHERE id=?",
            (title, notes, project_id, priority, due_date, task_id),
        )
        self.conn.commit()

    def toggle_task(self, task_id):
        self.conn.execute(
            "UPDATE tasks SET done = NOT done WHERE id=?", (task_id,)
        )
        self.conn.commit()

    def delete_task(self, task_id):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()


class TaskDialog(tk.Toplevel):

    def __init__(self, parent, projects, task=None, default_project_id=1):
        super().__init__(parent)
        self.title("تعديل مهمة" if task else "مهمة جديدة")
        self.resizable(False, False)
        self.transient(parent)
        self.result = None
        self.projects = {p["name"]: p["id"] for p in projects}

        pad = {"padx": 10, "pady": 5}
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text="عنوان المهمة *").grid(
            row=0, column=1, sticky="e", **pad
        )
        self.title_var = tk.StringVar(value=task["title"] if task else "")
        title_entry = ttk.Entry(
            frm, textvariable=self.title_var, width=40, justify="right"
        )
        title_entry.grid(row=0, column=0, sticky="ew", **pad)

        ttk.Label(frm, text="ملاحظات").grid(
            row=1, column=1, sticky="ne", **pad
        )
        self.notes = tk.Text(frm, width=40, height=4, font=FONT)
        self.notes.grid(row=1, column=0, sticky="ew", **pad)
        self.notes.tag_configure("rtl", justify="right")
        if task and task["notes"]:
            self.notes.insert("1.0", task["notes"], "rtl")

        ttk.Label(frm, text="الاستحقاق (YYYY-MM-DD)").grid(
            row=2, column=1, sticky="e", **pad
        )
        due = task["due_date"] if task and task["due_date"] else ""
        self.date_var = tk.StringVar(value=due)
        date_row = ttk.Frame(frm)
        date_row.grid(row=2, column=0, sticky="e", **pad)
        ttk.Entry(
            date_row, textvariable=self.date_var, width=14, justify="center"
        ).pack(side="right")
        ttk.Button(
            date_row,
            text="اليوم",
            width=6,
            command=lambda: self.date_var.set(date.today().isoformat()),
        ).pack(side="right", padx=4)
        ttk.Button(
            date_row, text="مسح", width=6, command=lambda: self.date_var.set("")
        ).pack(side="right")

        ttk.Label(frm, text="الأولوية").grid(
            row=3, column=1, sticky="e", **pad
        )
        cur_prio = task["priority"] if task else 4
        self.prio_var = tk.StringVar(value=PRIORITIES[cur_prio][0])
        ttk.Combobox(
            frm,
            textvariable=self.prio_var,
            state="readonly",
            justify="right",
            values=[name for _, (name, _) in PRIORITIES.items()],
        ).grid(row=3, column=0, sticky="ew", **pad)

        ttk.Label(frm, text="المشروع").grid(
            row=4, column=1, sticky="e", **pad
        )
        cur_proj = task["project_id"] if task else default_project_id
        proj_name = next(
            (n for n, i in self.projects.items() if i == cur_proj), "الوارد"
        )
        self.proj_var = tk.StringVar(value=proj_name)
        ttk.Combobox(
            frm,
            textvariable=self.proj_var,
            state="readonly",
            justify="right",
            values=list(self.projects),
        ).grid(row=4, column=0, sticky="ew", **pad)

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btns, text="حفظ", command=self._save).pack(
            side="right", padx=5
        )
        ttk.Button(btns, text="إلغاء", command=self.destroy).pack(
            side="right", padx=5
        )

        self.bind(
            "<Return>",
            lambda e: self._save() if e.widget is not self.notes else None,
        )
        self.bind("<Escape>", lambda e: self.destroy())

        title_entry.focus_set()
        self.grab_set()
        self.wait_window(self)

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning(
                APP_NAME, "الرجاء كتابة عنوان المهمة", parent=self
            )
            return

        due = self.date_var.get().strip()
        if due:
            try:
                due = datetime.strptime(due, "%Y-%m-%d").date().isoformat()
            except ValueError:
                messagebox.showwarning(
                    APP_NAME,
                    "صيغة التاريخ غير صحيحة، مثال: 2026-12-31",
                    parent=self,
                )
                return

        self.result = {
            "title": title,
            "notes": self.notes.get("1.0", "end").strip(),
            "due_date": due or None,
            "priority": PRIORITY_BY_NAME[self.prio_var.get()],
            "project_id": self.projects[self.proj_var.get()],
        }
        self.destroy()


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(f"✓ {APP_NAME}")
        self.geometry("900x560")
        self.minsize(720, 420)

        self.db = Database()
        self.current = ("view", "all")
        self.nav_items = []

        self._setup_style()
        self._build_ui()
        self.refresh()

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", font=FONT)
        style.configure("Treeview", rowheight=30, font=FONT)
        style.configure("Treeview.Heading", font=FONT_BOLD)

    def _build_ui(self):
        side = ttk.Frame(self, padding=8)
        side.pack(side="right", fill="y")

        ttk.Label(
            side,
            text=f"{APP_NAME}",
            font=("Tahoma", 16, "bold"),
            foreground="#db4c3f",
        ).pack(anchor="e", pady=(0, 8))

        self.nav = tk.Listbox(
            side,
            width=24,
            font=FONT,
            activestyle="none",
            exportselection=False,
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#fde3e0",
            selectforeground="#000",
        )
        self.nav.pack(fill="y", expand=True)
        self.nav.bind("<<ListboxSelect>>", self._on_nav_select)

        proj_btns = ttk.Frame(side)
        proj_btns.pack(fill="x", pady=(8, 0))
        ttk.Button(
            proj_btns, text="+ مشروع", command=self.add_project
        ).pack(side="right", expand=True, fill="x")
        ttk.Button(
            proj_btns, text="حذف المشروع", command=self.delete_project
        ).pack(side="right", expand=True, fill="x")

        main = ttk.Frame(self, padding=10)
        main.pack(side="left", fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x")

        self.heading = ttk.Label(top, text="", font=("Tahoma", 15, "bold"))
        self.heading.pack(side="right")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_tasks())
        ttk.Entry(
            top, textvariable=self.search_var, width=22, justify="right"
        ).pack(side="left")
        ttk.Label(top, text="بحث:").pack(side="left", padx=4)

        bar = ttk.Frame(main)
        bar.pack(fill="x", pady=8)
        ttk.Button(
            bar, text="مهمة جديدة (Ctrl+N)", command=self.add_task
        ).pack(side="right", padx=2)
        ttk.Button(bar, text="تعديل", command=self.edit_task).pack(
            side="right", padx=2
        )
        ttk.Button(bar, text="إنجاز / تراجع", command=self.toggle_task).pack(
            side="right", padx=2
        )
        ttk.Button(bar, text="حذف", command=self.delete_task).pack(
            side="right", padx=2
        )

        cols = ("project", "due", "priority", "title", "done")
        self.tree = ttk.Treeview(
            main, columns=cols, show="headings", selectmode="browse"
        )
        headings = {
            "done": ("", 40),
            "title": ("المهمة", 330),
            "priority": ("الأولوية", 80),
            "due": ("الموعد", 110),
            "project": ("المشروع", 110),
        }
        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text, anchor="e")
            self.tree.column(
                col,
                width=width,
                anchor="e",
                stretch=(col == "title"),
            )

        scroll = ttk.Scrollbar(main, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="left", fill="y")
        self.tree.pack(side="right", fill="both", expand=True)

        for num, (_, color) in PRIORITIES.items():
            self.tree.tag_configure(f"p{num}", foreground=color)
        self.tree.tag_configure("done", foreground="#9aa0a6")
        self.tree.tag_configure("overdue", background="#fdecea")

        self.tree.bind("<Double-1>", lambda e: self.edit_task())
        self.tree.bind("<Return>", lambda e: self.edit_task())
        self.tree.bind("<space>", lambda e: self.toggle_task())
        self.tree.bind("<Delete>", lambda e: self.delete_task())
        self.bind("<Control-n>", lambda e: self.add_task())

        self.status = ttk.Label(self, anchor="e", padding=(8, 2))
        self.status.pack(side="bottom", fill="x")

    def refresh(self):
        self.refresh_sidebar()
        self.refresh_tasks()

    def refresh_sidebar(self):
        counts = self.db.counts()
        self.nav_items = [
            ("view", key, f"{label} ({counts[key]})") for key, label in VIEWS
        ]
        for p in self.db.get_projects():
            self.nav_items.append(("project", p["id"], f"📁 {p['name']}"))

        self.nav.delete(0, "end")
        selected = 0
        for i, (kind, key, label) in enumerate(self.nav_items):
            self.nav.insert("end", label)
            if (kind, key) == self.current:
                selected = i
        self.nav.selection_set(selected)

    def refresh_tasks(self):
        kind, key = self.current
        view = key if kind == "view" else "all"
        project_id = key if kind == "project" else None

        tasks = self.db.get_tasks(
            view, project_id, self.search_var.get().strip()
        )

        if kind == "view":
            self.heading.config(text=dict(VIEWS)[key])
        else:
            name = next(
                (p["name"] for p in self.db.get_projects() if p["id"] == key),
                "",
            )
            self.heading.config(text=name)

        today = date.today().isoformat()
        self.tree.delete(*self.tree.get_children())
        for t in tasks:
            prio_name = PRIORITIES[t["priority"]][0]
            overdue = bool(
                t["due_date"] and t["due_date"] < today and not t["done"]
            )
            due_text = (
                f"{t['due_date']} (متأخرة)" if overdue else (t["due_date"] or "")
            )

            tags = ["done"] if t["done"] else [f"p{t['priority']}"]
            if overdue:
                tags.append("overdue")

            self.tree.insert(
                "",
                "end",
                iid=str(t["id"]),
                tags=tags,
                values=(
                    t["project_name"],
                    due_text,
                    prio_name,
                    t["title"],
                    "✓" if t["done"] else "○",
                ),
            )

        self.status.config(text=f"عدد المهام المعروضة: {len(tasks)}")

    def _on_nav_select(self, _event):
        sel = self.nav.curselection()
        if sel:
            kind, key, _ = self.nav_items[sel[0]]
            self.current = (kind, key)
            self.refresh_tasks()

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def add_task(self):
        default_proj = self.current[1] if self.current[0] == "project" else 1
        dlg = TaskDialog(
            self, self.db.get_projects(), default_project_id=default_proj
        )
        if dlg.result:
            self.db.add_task(**dlg.result)
            self.refresh()

    def edit_task(self):
        task_id = self._selected_id()
        if task_id is None:
            return
        dlg = TaskDialog(
            self, self.db.get_projects(), task=self.db.get_task(task_id)
        )
        if dlg.result:
            self.db.update_task(task_id, **dlg.result)
            self.refresh()

    def toggle_task(self):
        task_id = self._selected_id()
        if task_id is not None:
            self.db.toggle_task(task_id)
            self.refresh()

    def delete_task(self):
        task_id = self._selected_id()
        if task_id is not None and messagebox.askyesno(
            APP_NAME, "حذف هذه المهمة نهائياً؟"
        ):
            self.db.delete_task(task_id)
            self.refresh()

    def add_project(self):
        name = simpledialog.askstring(
            APP_NAME, "اسم المشروع الجديد:", parent=self
        )
        if name and name.strip():
            self.db.add_project(name.strip())
            self.refresh()

    def delete_project(self):
        kind, key = self.current
        if kind != "project":
            messagebox.showinfo(APP_NAME, "اختر مشروعاً من القائمة أولاً.")
        elif key == 1:
            messagebox.showinfo(APP_NAME, "لا يمكن حذف مشروع الوارد الأساسي.")
        elif messagebox.askyesno(
            APP_NAME, "حذف المشروع؟ ستنتقل مهامه إلى الوارد."
        ):
            self.db.delete_project(key)
            self.current = ("view", "all")
            self.refresh()


if __name__ == "__main__":
    App().mainloop()