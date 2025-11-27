# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
from typing import Dict, List

from task_manager import TaskManager, PRIORITY_LEVELS
from analytics import show_analytics_tk  # unchanged import


class TodoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Smart To-Do - Analytics")
        self.tm = TaskManager()
        self.sort_column = None
        self.sort_reverse = False
        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        frm_inputs = ttk.Frame(self.root, padding=8)
        frm_inputs.pack(fill="x")

        ttk.Label(frm_inputs, text="Task:").grid(row=0, column=0, sticky="w")
        self.entry_title = ttk.Entry(frm_inputs, width=40)
        self.entry_title.grid(row=0, column=1, sticky="w", padx=(4, 0))

        ttk.Label(frm_inputs, text="Due (YYYY-MM-DD):").grid(row=1, column=0, sticky="w")
        frm_due = ttk.Frame(frm_inputs)
        frm_due.grid(row=1, column=1, sticky="w", padx=(4, 0))
        self.entry_due = ttk.Entry(frm_due, width=15)
        self.entry_due.pack(side="left", padx=(0, 4))
        ttk.Button(frm_due, text="📅 Pick", command=self.on_pick_due_date).pack(side="left")

        ttk.Label(frm_inputs, text="Priority:").grid(row=2, column=0, sticky="w")
        self.entry_priority = ttk.Combobox(frm_inputs, values=list(PRIORITY_LEVELS), width=18)
        self.entry_priority.set("Normal")
        self.entry_priority.grid(row=2, column=1, sticky="w", padx=(4, 0))

        # Notes input for quick add
        ttk.Label(frm_inputs, text="Notes:").grid(row=3, column=0, sticky="nw", pady=(6,0))
        self.entry_notes = tk.Text(frm_inputs, width=50, height=3)
        self.entry_notes.grid(row=3, column=1, sticky="w", padx=(4,0), pady=(6,0))
        
        frm_buttons = ttk.Frame(self.root, padding=6)
        frm_buttons.pack(fill="x")
        ttk.Button(frm_buttons, text="Add", command=self.on_add_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Edit", command=self.on_edit_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Complete", command=self.on_complete_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Delete", command=self.on_delete_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Bulk Complete", command=self.on_bulk_complete).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Bulk Delete", command=self.on_bulk_delete).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Snooze", command=self.on_snooze_preset_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Analytics", command=self.on_analytics_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Sync", command=self.on_sync_click).pack(side="left", padx=4)
        ttk.Button(frm_buttons, text="Refresh", command=self.refresh_list).pack(side="left", padx=4)

        # Treeview with urgency and due-status columns
        # include notes column (short preview) and keep an accessible cols list
        self.cols = ("id", "title", "notes", "due_date", "priority", "status", "urgency", "due_status")
        cols = self.cols[:]
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", selectmode="extended")
        headings = [
            ("id", 60), ("title", 280), ("notes", 200), ("due_date", 110),
            ("priority", 100), ("status", 100), ("urgency", 80), ("due_status", 100)
        ]
        for c, w in headings:
            col_anchor = "w" if c == "title" else "center"
            heading_anchor = "center"
            self.tree.heading(c, text=c.replace("_", " ").title(), anchor=heading_anchor, command=lambda col=c: self.on_column_click(col))
            self.tree.column(c, width=w, anchor=col_anchor)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        # Row tags for styling
        # stronger colors for urgency/due-status
        self.tree.tag_configure("very_overdue", background="#ff4d4d")   # red
        self.tree.tag_configure("overdue", background="#ffb3b3")        # light red
        self.tree.tag_configure("due_soon", background="#ffcc99")      # orange
        self.tree.tag_configure("urgent", background="#fff2cc")        # yellow
        self.tree.tag_configure("completed", background="#ccffcc")     # green
        self.tree.tag_configure("normal", background="")

        # Bind double-click to quick snooze (example)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Search/filter bar
        frm_search = ttk.Frame(self.root, padding=8)
        frm_search.pack(fill="x")
        ttk.Label(frm_search, text="Search:").grid(row=0, column=0, sticky="w")
        self.entry_search = ttk.Entry(frm_search, width=40)
        self.entry_search.grid(row=0, column=1, sticky="w", padx=(4, 0))
        self.entry_search.bind("<KeyRelease>", self.refresh_list)

    def on_column_click(self, column):
        """Sort by clicked column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_list()

    def refresh_list(self, event=None):
        for i in self.tree.get_children():
            self.tree.delete(i)

        search_term = self.entry_search.get().lower()
        tasks = self.tm.tasks[:]
        
        # Filter by search term
        # include notes in filtering
        filtered_tasks = [t for t in tasks if (
            search_term in (t.title or "").lower() or 
            search_term in (getattr(t, "priority_level", "Normal") or "").lower() or 
            search_term in (t.status or "").lower() or
            search_term in (getattr(t, "notes", "") or "").lower()
        )]
        
        # Sort if column selected
        if self.sort_column:
            if self.sort_column == "due_date":
                filtered_tasks.sort(key=lambda t: t.due_date or "", reverse=self.sort_reverse)
            elif self.sort_column == "urgency":
                filtered_tasks.sort(key=lambda t: self.tm.compute_urgency_score(t), reverse=self.sort_reverse)
            elif self.sort_column == "priority":
                filtered_tasks.sort(key=lambda t: getattr(t, "priority_level", "Normal") or "", reverse=self.sort_reverse)
            elif self.sort_column == "status":
                filtered_tasks.sort(key=lambda t: t.status or "", reverse=self.sort_reverse)
            elif self.sort_column == "title":
                filtered_tasks.sort(key=lambda t: t.title or "", reverse=self.sort_reverse)

        # Use TaskManager's in-memory list
        for t in filtered_tasks:
            tid = t.task_id
            title = t.title
            notes = (getattr(t, "notes", "") or "").replace("\n", " ")[:150]
            due = t.due_date or ""
            priority = getattr(t, "priority_level", "Normal")
            status = t.status
            # compute urgency score and due status
            urgency_score = self.tm.compute_urgency_score(t)
            due_status = ""
            # overdue flag with granularity
            try:
                if t.due_date:
                    d = datetime.fromisoformat(t.due_date).date()
                    if status != "Completed" and d < date.today():
                        days_past = (date.today() - d).days
                        if days_past >= 7:
                            due_status = "Very Overdue"
                        else:
                            due_status = "Overdue"
                    elif status != "Completed" and (d - date.today()).days <= 3:
                        due_status = "Due Soon"
            except Exception:
                due_status = ""

            # decide tag
            tag = "normal"
            if due_status == "Very Overdue":
                tag = "very_overdue"
            elif due_status == "Overdue":
                tag = "overdue"
            elif due_status == "Due Soon":
                tag = "due_soon"
            if status == "Completed":
                tag = "completed"
            elif urgency_score >= 5.0 and tag == "normal":
                tag = "urgent"

            if (search_term in title.lower() or 
                search_term in priority.lower() or 
                search_term in status.lower() or
                search_term in notes.lower()):
                # insert values matching self.cols order
                vals = (tid, title, notes, due, priority, status, f"{urgency_score:.2f}", due_status)
                self.tree.insert("", "end", values=vals, tags=(tag,))

    def on_add_click(self):
        title = self.entry_title.get().strip()
        due = self.entry_due.get().strip()
        priority = self.entry_priority.get().strip() or "Normal"
        notes = self.entry_notes.get("1.0", tk.END).strip()

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

        # Try to pass notes into TaskManager.add_task if it supports it,
        # otherwise fallback to setting notes on the in-memory task.
        try:
            # many implementations: add_task(title, due_date, priority, status, **kwargs)
            task_obj = self.tm.add_task(title, due or None, priority, "Pending", notes=notes)
        except TypeError:
            # older signature without notes
            task_obj = self.tm.add_task(title, due or None, priority, "Pending")
            # try to set notes on last task in-memory
            try:
                if hasattr(self.tm, "tasks") and self.tm.tasks:
                    last = self.tm.tasks[-1]
                    setattr(last, "notes", notes)
            except Exception:
                pass
        except Exception:
            # generic fallback to attempt add without notes
            task_obj = self.tm.add_task(title, due or None, priority, "Pending")
            try:
                if hasattr(self.tm, "tasks") and self.tm.tasks:
                    last = self.tm.tasks[-1]
                    setattr(last, "notes", notes)
            except Exception:
                pass

        # clear inputs including notes
        self.entry_title.delete(0, tk.END)
        self.entry_due.delete(0, tk.END)
        self.entry_priority.set("Normal")
        try:
            self.entry_notes.delete("1.0", tk.END)
        except Exception:
            pass
        self.refresh_list()

    def _get_selected_task_ids(self):
        """Return list of selected task IDs."""
        sel = self.tree.selection()
        task_ids = []
        for item in sel:
            vals = self.tree.item(item)["values"]
            if vals:
                try:
                    task_ids.append(int(vals[0]) if vals[0] is not None else None)
                except Exception:
                    continue
        return [tid for tid in task_ids if tid is not None]

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

    def _find_task_by_id(self, task_id):
        """Return the task object from in-memory list, or None."""
        for t in getattr(self.tm, "tasks", []) or []:
            try:
                if getattr(t, "task_id", None) == task_id:
                    return t
            except Exception:
                continue
        return None

    def on_snooze_preset_click(self):
        """Show snooze preset menu with common durations."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showinfo("Info", "Select a task to snooze.")
            return
        
        snooze_win = tk.Toplevel(self.root)
        snooze_win.title("Snooze Task")
        snooze_win.transient(self.root)
        snooze_win.grab_set()
        snooze_win.geometry("300x200")

        ttk.Label(snooze_win, text="Snooze by:", font=("Arial", 10, "bold")).pack(pady=10)
        
        presets = [
            ("1 day", 1),
            ("3 days", 3),
            ("1 week", 7),
            ("2 weeks", 14),
            ("1 month", 30),
        ]
        
        def snooze_by(days):
            res = self.tm.snooze_task(task_id, days=days)
            if res:
                messagebox.showinfo("Snoozed", f"Task snoozed by {days} day(s). New due: {res.due_date}")
                snooze_win.destroy()
                self.refresh_list()
            else:
                messagebox.showwarning("Snooze", "Failed to snooze task.")
        
        for label, days in presets:
            ttk.Button(snooze_win, text=label, command=lambda d=days: snooze_by(d)).pack(fill="x", padx=10, pady=4)
        
        ttk.Separator(snooze_win, orient="horizontal").pack(fill="x", padx=10, pady=10)
        
        ttk.Label(snooze_win, text="Custom days:").pack(pady=5)
        spin_days = ttk.Spinbox(snooze_win, from_=1, to=365, width=10)
        spin_days.set(1)
        spin_days.pack(pady=5)
        
        ttk.Button(snooze_win, text="Apply Custom", command=lambda: snooze_by(int(spin_days.get()))).pack(pady=10)

    def on_edit_click(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showinfo("Info", "Select a task to edit.")
            return

        t = self._find_task_by_id(task_id)
        if not t:
            messagebox.showwarning("Edit", f"Task {task_id} not found in memory.")
            return

        # Create modal edit window
        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Edit Task {task_id}")
        edit_win.transient(self.root)
        edit_win.grab_set()

        ttk.Label(edit_win, text="Task:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        e_title = ttk.Entry(edit_win, width=40)
        e_title.grid(row=0, column=1, padx=6, pady=6)
        e_title.insert(0, getattr(t, "title", "") or "")

        ttk.Label(edit_win, text="Due (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        frm_due_edit = ttk.Frame(edit_win)
        frm_due_edit.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        e_due = ttk.Entry(frm_due_edit, width=20)
        e_due.pack(side="left")
        e_due.insert(0, getattr(t, "due_date", "") or "")
        ttk.Button(frm_due_edit, text="📅", width=3, command=lambda: self._open_edit_date_picker(edit_win, e_due)).pack(side="left", padx=(6,0))

        ttk.Label(edit_win, text="Priority:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        e_priority = ttk.Combobox(edit_win, values=list(PRIORITY_LEVELS), width=18)
        e_priority.grid(row=2, column=1, padx=6, pady=6)
        e_priority.set(getattr(t, "priority_level", "Normal") or "Normal")

        ttk.Label(edit_win, text="Status:").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        e_status = ttk.Combobox(edit_win, values=["Pending", "Completed"], width=18)
        e_status.grid(row=3, column=1, padx=6, pady=6)
        e_status.set(getattr(t, "status", "Pending") or "Pending")

        ttk.Label(edit_win, text="Notes:").grid(row=4, column=0, sticky="nw", padx=6, pady=6)
        e_notes = tk.Text(edit_win, width=40, height=4)
        e_notes.grid(row=4, column=1, padx=6, pady=6)
        e_notes.insert("1.0", getattr(t, "notes", "") or "")

        def save_changes(event=None):
            new_title = e_title.get().strip()
            new_due = e_due.get().strip()
            new_prio = e_priority.get().strip() or "Normal"
            new_status = e_status.get().strip() or "Pending"
            new_notes = e_notes.get("1.0", tk.END).strip()

            if not new_title:
                messagebox.showwarning("Validation", "Task title is required.", parent=edit_win)
                return
            if new_due:
                try:
                    datetime.fromisoformat(new_due)
                except Exception:
                    messagebox.showwarning("Validation", "Due date must be YYYY-MM-DD or blank.", parent=edit_win)
                    return

            try:
                if hasattr(self.tm, "update_task"):
                    # safely attempt to update via TaskManager; include 'priority' param
                    try:
                        self.tm.update_task(task_id, title=new_title, due_date=new_due or None, priority=new_prio, status=new_status)
                    except TypeError:
                        # fallback if update_task expects different arg names
                        self.tm.update_task(task_id, title=new_title, due_date=new_due or None, priority_level=new_prio, status=new_status)
                else:
                    setattr(t, "title", new_title)
                    setattr(t, "due_date", new_due or None)
                    setattr(t, "priority_level", new_prio)
                    setattr(t, "status", new_status)
                # ensure in-memory notes/priority are stored
                setattr(t, "notes", new_notes)
                setattr(t, "priority_level", new_prio)
            except Exception as ex:
                messagebox.showerror("Edit Error", f"Failed to update task: {ex}", parent=edit_win)
                return

            edit_win.grab_release()
            edit_win.destroy()
            self.refresh_list()

        btn_frame = ttk.Frame(edit_win)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(6,12))
        ttk.Button(btn_frame, text="Save", command=save_changes).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", command=lambda: (edit_win.grab_release(), edit_win.destroy())).pack(side="left", padx=6)

        edit_win.bind("<Return>", save_changes)
        e_title.focus_set()

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

    def on_bulk_complete(self):
        task_ids = self._get_selected_task_ids()
        if not task_ids:
            messagebox.showinfo("Info", "Select tasks to mark complete.")
            return
        if not messagebox.askyesno("Confirm", f"Mark {len(task_ids)} task(s) as complete?"):
            return
        for tid in task_ids:
            self.tm.complete_task(tid)
        self.refresh_list()

    def on_bulk_delete(self):
        task_ids = self._get_selected_task_ids()
        if not task_ids:
            messagebox.showinfo("Info", "Select tasks to delete.")
            return
        if not messagebox.askyesno("Confirm", f"Delete {len(task_ids)} task(s)?"):
            return
        for tid in task_ids:
            self.tm.delete_task(tid)
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

    def on_pick_due_date(self):
        """Open a simple date picker dialog."""
        date_win = tk.Toplevel(self.root)
        date_win.title("Pick Due Date")
        date_win.transient(self.root)
        date_win.grab_set()
        date_win.geometry("300x200")

        ttk.Label(date_win, text="Year:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        spin_year = ttk.Spinbox(date_win, from_=2024, to=2030, width=10)
        spin_year.set(date.today().year)
        spin_year.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(date_win, text="Month:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        spin_month = ttk.Spinbox(date_win, from_=1, to=12, width=10)
        spin_month.set(date.today().month)
        spin_month.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(date_win, text="Day:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        spin_day = ttk.Spinbox(date_win, from_=1, to=31, width=10)
        spin_day.set(date.today().day)
        spin_day.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        def apply_date():
            try:
                year = int(spin_year.get())
                month = int(spin_month.get())
                day = int(spin_day.get())
                selected_date = date(year, month, day)
                self.entry_due.delete(0, tk.END)
                self.entry_due.insert(0, selected_date.isoformat())
                date_win.destroy()
            except Exception as ex:
                messagebox.showerror("Date Error", f"Invalid date: {ex}", parent=date_win)

        ttk.Button(date_win, text="Apply", command=apply_date).grid(row=3, column=0, columnspan=2, pady=12)

    def on_tree_double_click(self, event):
        """Handle double-click on tree cell for inline quick edit or snooze."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        
        col = self.tree.identify_column(event.x)
        sel = self.tree.selection()
        if not sel:
            return
        # map column number -> column name using self.cols
        try:
            col_index = int(col.replace("#", "")) - 1
            col_name = self.cols[col_index]
        except Exception:
            col_name = None

        task_id = self._get_selected_task_id()
        if not task_id:
            return
        # Double-click on status column: toggle complete
        if col_name == "status":
            self.tm.complete_task(task_id)
            self.refresh_list()
            return
        
        # Default: snooze by 1 day
        res = self.tm.snooze_task(task_id, days=1)
        if res:
            messagebox.showinfo("Quick Snooze", f"Task {task_id} snoozed to {res.due_date}")
            self.refresh_list()

    def _open_edit_date_picker(self, parent_win, entry_widget):
        """Open a date picker Toplevel scoped to the edit window and set entry_widget."""
        date_win = tk.Toplevel(parent_win)
        date_win.title("Pick Due Date")
        date_win.transient(parent_win)
        date_win.grab_set()
        ttk.Label(date_win, text="Year:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        spin_year = ttk.Spinbox(date_win, from_=2024, to=2030, width=10)
        spin_year.set(date.today().year)
        spin_year.grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(date_win, text="Month:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        spin_month = ttk.Spinbox(date_win, from_=1, to=12, width=10)
        spin_month.set(date.today().month)
        spin_month.grid(row=1, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(date_win, text="Day:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        spin_day = ttk.Spinbox(date_win, from_=1, to=31, width=10)
        spin_day.set(date.today().day)
        spin_day.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        def apply_date():
            try:
                year = int(spin_year.get())
                month = int(spin_month.get())
                day = int(spin_day.get())
                selected_date = date(year, month, day)
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, selected_date.isoformat())
                date_win.destroy()
            except Exception as ex:
                messagebox.showerror("Date Error", f"Invalid date: {ex}", parent=date_win)

        ttk.Button(date_win, text="Apply", command=apply_date).grid(row=3, column=0, columnspan=2, pady=12)

def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()