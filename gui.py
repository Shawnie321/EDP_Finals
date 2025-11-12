# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import Dict, List

from task_manager import TaskManager, PRIORITY_LEVELS
from analytics import show_analytics_tk  # unchanged import


class TodoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Smart To-Do - Analytics")
        self.tm = TaskManager()
        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        frm_inputs = ttk.Frame(self.root, padding=8)
        frm_inputs.pack(fill="x")

        ttk.Label(frm_inputs, text="Task:").grid(row=0, column=0, sticky="w")
        self.entry_title = ttk.Entry(frm_inputs, width=40)
        self.entry_title.grid(row=0, column=1, sticky="w", padx=(4, 0))

        ttk.Label(frm_inputs, text="Due (YYYY-MM-DD):").grid(row=1, column=0, sticky="w")
        self.entry_due = ttk.Entry(frm_inputs, width=20)
        self.entry_due.grid(row=1, column=1, sticky="w", padx=(4, 0))

        ttk.Label(frm_inputs, text="Priority:").grid(row=2, column=0, sticky="w")
        self.entry_priority = ttk.Combobox(frm_inputs, values=list(PRIORITY_LEVELS), width=18)
        self.entry_priority.set("Normal")
        self.entry_priority.grid(row=2, column=1, sticky="w", padx=(4, 0))

        frm_buttons = ttk.Frame(self.root, padding=6)
        frm_buttons.pack(fill="x")
        ttk.Button(frm_buttons, text="Add", command=self.on_add_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Complete", command=self.on_complete_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Delete", command=self.on_delete_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Analytics", command=self.on_analytics_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Sync", command=self.on_sync_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Refresh", command=self.refresh_list).pack(side="left", padx=4)

        # Extra controls for priority and snooze
        frm_extra = ttk.Frame(self.root, padding=6)
        frm_extra.pack(fill="x")
        ttk.Label(frm_extra, text="Set Priority:").pack(side="left", padx=(4, 2))
        self.cmb_set_priority = ttk.Combobox(frm_extra, values=list(PRIORITY_LEVELS), width=12)
        self.cmb_set_priority.set("Normal")
        self.cmb_set_priority.pack(side="left", padx=(0, 8))
        ttk.Button(frm_extra, text="Apply Priority", command=self.on_set_priority_click).pack(side="left", padx=4)

        ttk.Label(frm_extra, text="Snooze days:").pack(side="left", padx=(12, 2))
        self.spin_snooze = ttk.Spinbox(frm_extra, from_=1, to=30, width=5)
        self.spin_snooze.set("1")
        self.spin_snooze.pack(side="left", padx=(0, 8))
        ttk.Button(frm_extra, text="Snooze", command=self.on_snooze_click).pack(side="left", padx=4)

        # Treeview with urgency and due-status columns
        cols = ("id", "title", "due_date", "priority", "status", "urgency", "due_status")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", selectmode="browse")
        headings = [
            ("id", 60), ("title", 320), ("due_date", 110),
            ("priority", 100), ("status", 100), ("urgency", 80), ("due_status", 100)
        ]
        for c, w in headings:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        # Row tags for styling
        self.tree.tag_configure("overdue", background="#ffcccc")
        self.tree.tag_configure("urgent", background="#fff2cc")
        self.tree.tag_configure("completed", background="#ccffcc")
        self.tree.tag_configure("normal", background="")

        # Bind double-click to quick snooze (example)
        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Use TaskManager's in-memory list
        for t in self.tm.tasks:
            tid = t.task_id
            title = t.title
            due = t.due_date or ""
            priority = getattr(t, "priority_level", "Normal")
            status = t.status
            # compute urgency score and due status
            urgency_score = self.tm.compute_urgency_score(t)
            due_status = ""
            # overdue flag
            try:
                if t.due_date:
                    d = datetime.fromisoformat(t.due_date).date()
                    if status != "Completed" and d < date.today():
                        due_status = "Overdue"
                    elif status != "Completed" and (d - date.today()).days <= 3:
                        due_status = "Due Soon"
            except Exception:
                due_status = ""

            # decide tag
            tag = "normal"
            if due_status == "Overdue":
                tag = "overdue"
            if status == "Completed":
                tag = "completed"
            elif urgency_score >= 5.0:
                tag = "urgent"

            self.tree.insert("", "end", values=(tid, title, due, priority, status, f"{urgency_score:.2f}", due_status), tags=(tag,))

    def on_add_click(self):
        title = self.entry_title.get().strip()
        due = self.entry_due.get().strip()
        priority = self.entry_priority.get().strip() or "Normal"

        if not title:
            messagebox.showwarning("Validation", "Task title is required.")
            return

        # Validate due date format (basic)
        if due:
            try:
                datetime.fromisoformat(due)
            except Exception:
                messagebox.showwarning("Validation", "Due date must be YYYY-MM-DD or blank.")
                return

        self.tm.add_task(title, due or None, priority, "Pending")
        self.entry_title.delete(0, tk.END)
        self.entry_due.delete(0, tk.END)
        self.entry_priority.set("Normal")
        self.refresh_list()

    def _get_selected_task_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0])["values"]
        if not vals:
            return None
        try:
            return int(vals[0]) if vals[0] is not None else None
        except Exception:
            return None

    def on_complete_click(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showinfo("Info", "Select a task to mark complete.")
            return
        self.tm.complete_task(task_id)
        self.refresh_list()

    def on_delete_click(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showinfo("Info", "Select a task to delete.")
            return
        if not messagebox.askyesno("Confirm", f"Delete task id {task_id}?"):
            return
        self.tm.delete_task(task_id)
        self.refresh_list()

    def on_set_priority_click(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showinfo("Info", "Select a task to set priority.")
            return
        new_prio = self.cmb_set_priority.get().strip() or "Normal"
        updated = self.tm.set_priority(task_id, new_prio)
        if updated:
            messagebox.showinfo("Priority", f"Task {task_id} priority set to {new_prio}.")
        else:
            messagebox.showwarning("Priority", "Failed to set priority.")
        self.refresh_list()

    def on_snooze_click(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showinfo("Info", "Select a task to snooze.")
            return
        try:
            days = int(self.spin_snooze.get())
        except Exception:
            days = 1
        res = self.tm.snooze_task(task_id, days=days)
        if res:
            messagebox.showinfo("Snooze", f"Task {task_id} snoozed by {days} day(s). New due: {res.due_date}")
        else:
            messagebox.showwarning("Snooze", "Failed to snooze task (ensure it has a valid due date).")
        self.refresh_list()

    def on_double_click(self, _event):
        """
        Quick double-click action: snooze by 1 day for selected task.
        """
        task_id = self._get_selected_task_id()
        if not task_id:
            return
        res = self.tm.snooze_task(task_id, days=1)
        if res:
            messagebox.showinfo("Quick Snooze", f"Task {task_id} snoozed to {res.due_date}")
            self.refresh_list()

    def on_sync_click(self):
        # Run a simple sync and show a brief report
        summary = self.tm.sync_with_remote(prefer_local=True)
        messagebox.showinfo("Sync complete", f"Pushed: {summary.get('pushed',0)}\nPulled: {summary.get('pulled',0)}\nUpdated: {summary.get('updated',0)}")
        self.refresh_list()

    def on_analytics_click(self):
        # Pass TaskManager instance so analytics can use DB helpers or local tasks
        try:
            show_analytics_tk(self.tm, parent=self.root, days_back=14)
        except Exception as ex:
            messagebox.showerror("Analytics Error", f"Failed to open analytics: {ex}")


def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()