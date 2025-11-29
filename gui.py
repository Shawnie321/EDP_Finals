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
        # give a modern default size
        try:
            self.root.geometry("1000x640")
        except Exception:
            pass
        self.tm = TaskManager()
        self.sort_column = None
        self.sort_reverse = False
        self.current_theme = "light"  # default theme
        self.style = ttk.Style(self.root)
        # prefer a theme that respects custom heading colors on most platforms
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self._init_styles()
        self._build_ui()
        self._apply_theme(self.current_theme)
        self.refresh_list()

    def _init_styles(self):
        """Initialize ttk styles for a modern light/dark look."""
        # Base font
        default_font = ("Segoe UI", 10)
        bold_font = ("Segoe UI Semibold", 10)
        heading_font = ("Segoe UI Semibold", 11)

        self.style.configure("Modern.TFrame", background="#f3f3f3")
        self.style.configure("Sidebar.TFrame", background="#ffffff")
        self.style.configure("Header.TLabel", font=heading_font, background="#f3f3f3")
        self.style.configure("SubHeader.TLabel", font=bold_font, background="#ffffff")
        self.style.configure("Modern.TLabel", font=default_font, background="#f3f3f3")
        self.style.configure("Modern.TEntry", font=default_font)
        self.style.configure("Accent.TButton", foreground="#ffffff", background="#0078D7", font=bold_font)
        self.style.map("Accent.TButton", background=[("active", "#106ebe")])
        # Toggle button style (explicit black text as requested)
        self.style.configure("Toggle.TButton", foreground="#000000", background="#e6e6e6", font=bold_font)
        self.style.map("Toggle.TButton", background=[("active", "#d4d4d4")])
        # Icon button style (small, flat)
        self.style.configure("Icon.TButton", foreground="#000000", background="#e6e6e6", font=("Segoe UI Semibold", 9), padding=4)
        self.style.map("Icon.TButton", background=[("active", "#d4d4d4")])

        # Treeview styling (headings & rows)
        self.style.configure("Modern.Treeview", font=default_font, rowheight=28, background="#ffffff", fieldbackground="#ffffff")
        self.style.configure("Modern.Treeview.Heading", font=bold_font)
        try:
            self.style.layout("Treeheading.Cell", self.style.layout("Treeheading.Cell"))
        except Exception:
            pass

    def _apply_theme(self, mode: str):
        """Apply colors for 'light' or 'dark' theme."""
        if mode == "dark":
            root_bg = "#1e1e1e"
            sidebar_bg = "#252526"
            panel_bg = "#2d2d30"
            fg = "#ffffff"
            heading_bg = "#2b2b2b"
            tree_bg = "#252526"
            row_bg = "#2d2d30"
            selection_bg = "#0078D7"
        else:
            # light
            root_bg = "#f3f3f3"
            sidebar_bg = "#ffffff"
            panel_bg = "#ffffff"
            fg = "#000000"
            heading_bg = "#f3f3f3"
            tree_bg = "#ffffff"
            row_bg = "#ffffff"
            selection_bg = "#0078D7"

        self.style.configure("Modern.TFrame", background=root_bg)
        self.style.configure("Sidebar.TFrame", background=sidebar_bg)
        self.style.configure("Modern.TLabel", background=root_bg, foreground=fg)
        self.style.configure("Header.TLabel", background=root_bg, foreground=fg)
        self.style.configure("SubHeader.TLabel", background=sidebar_bg, foreground=fg)
        self.style.configure("Modern.TEntry", fieldbackground=panel_bg, background=panel_bg, foreground=fg)
        self.style.configure("Accent.TButton", background=selection_bg, foreground="#ffffff")
        # ensure toggle button text color is black as requested
        try:
            self.style.configure("Toggle.TButton", foreground="#000000")
        except Exception:
            pass

        # Treeview colors
        self.style.configure("Modern.Treeview", background=tree_bg, fieldbackground=tree_bg, foreground=fg)
        self.style.configure("Modern.Treeview.Heading", background=heading_bg, foreground=fg)
        # tag colors for rows - keep clear contrasts
        if mode == "dark":
            self.tree_tag_colors = {"overdue": "#5a1515", "due_soon": "#5a4300", "completed": "#155a2a", "urgent": "#5a2b00", "normal": row_bg}
        else:
            self.tree_tag_colors = {"overdue": "#ffcccc", "due_soon": "#fff2cc", "completed": "#ccffcc", "urgent": "#ffe6cc", "normal": row_bg}

        try:
            self.root.configure(bg=root_bg)
        except Exception:
            pass

        # if tree exists, reconfigure its tags
        if hasattr(self, "tree"):
            for tag, color in self.tree_tag_colors.items():
                try:
                    self.tree.tag_configure(tag, background=color)
                except Exception:
                    pass
        # update notes text widget colors to match theme
        try:
            if hasattr(self, "entry_notes"):
                self.entry_notes.config(bg=panel_bg, fg=fg, insertbackground=fg)
                # ensure left pane does not allow widgets to overflow
                try:
                    left.update_idletasks()
                except Exception:
                    pass
        except Exception:
            pass

    def _toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self._apply_theme(self.current_theme)
        # update the icon to reflect the action (show moon when in light mode to switch to dark)
        try:
            if hasattr(self, "theme_icon_btn"):
                self.theme_icon_btn.config(text=("🌙" if self.current_theme == "light" else "☀️"))
        except Exception:
            pass
        self.refresh_list()

    def _build_ui(self):
        # Main container
        container = ttk.Frame(self.root, style="Modern.TFrame", padding=8)
        container.pack(fill="both", expand=True)

        # Use a PanedWindow to separate left and right panes so widgets cannot overlap
        paned = ttk.Panedwindow(container, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        # Left sidebar for inputs and actions (fixed minsize)
        left = ttk.Frame(paned, style="Sidebar.TFrame", width=320)
        left.pack_propagate(False)
        paned.add(left, weight=0)

        # Right content area will be a pane so it always sits beside left
        right = ttk.Frame(paned, style="Modern.TFrame")
        paned.add(right, weight=1)

        # Header and theme toggle (kept at top of container)
        header_frame = ttk.Frame(container, style="Modern.TFrame")
        header_frame.place(relx=0.5, rely=0.01, anchor="n")

        ttk.Label(left, text="Smart To-Do List", style="Header.TLabel", anchor="w").pack(fill="x", padx=12, pady=(12, 6))

        # Theme icon button placed in upper-right of the root window.
        # Use a tk.Button for reliable bg/fg rendering across platforms.
        if self.current_theme == "dark":
            icon_bg = "#3a3a3a"
            icon_fg = "#ffffff"
        else:
            icon_bg = "#e6e6e6"
            icon_fg = "#000000"
        icon_text = ("🌙" if self.current_theme == "light" else "☀️")
        icon_btn = tk.Button(self.root, text=icon_text, command=self._toggle_theme, bd=0, relief="flat", bg=icon_bg, fg=icon_fg, activebackground=icon_bg, activeforeground=icon_fg)
        # place near the upper-right corner of the root with a small margin
        icon_btn.place(relx=1.0, x=-12, y=12, anchor="ne")
        self.theme_icon_btn = icon_btn

        # Inputs
        inp_frame = ttk.Frame(left, style="Sidebar.TFrame")
        inp_frame.pack(fill="both", expand=False, padx=12, pady=(6,0))
        inp_frame.columnconfigure(1, weight=1)

        ttk.Label(inp_frame, text="Task:", style="SubHeader.TLabel").grid(row=0, column=0, sticky="w")
        self.entry_title = ttk.Entry(inp_frame, style="Modern.TEntry")
        self.entry_title.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=4)

        ttk.Label(inp_frame, text="Due (YYYY-MM-DD):", style="SubHeader.TLabel").grid(row=1, column=0, sticky="w")
        frm_due = ttk.Frame(inp_frame, style="Sidebar.TFrame")
        frm_due.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=4)
        self.entry_due = ttk.Entry(frm_due, width=18, style="Modern.TEntry")
        self.entry_due.pack(side="left")
        ttk.Button(frm_due, text="📅", width=3, command=self.on_pick_due_date).pack(side="left", padx=(6, 0))

        ttk.Label(inp_frame, text="Priority:", style="SubHeader.TLabel").grid(row=2, column=0, sticky="w")
        self.entry_priority = ttk.Combobox(inp_frame, values=list(PRIORITY_LEVELS), width=18)
        self.entry_priority.set("Normal")
        self.entry_priority.grid(row=2, column=1, sticky="w", padx=(6, 0), pady=4)

        ttk.Label(inp_frame, text="Notes:", style="SubHeader.TLabel").grid(row=3, column=0, sticky="nw", pady=(6, 0))
        # add a visible 1px border for the notes box (relief solid) and make it expand within left pane
        self.entry_notes = tk.Text(inp_frame, height=6, bd=1, relief="solid", highlightthickness=0)
        self.entry_notes.grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))

        # Action buttons grouped
        btn_frame = ttk.Frame(left, style="Sidebar.TFrame")
        btn_frame.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Button(btn_frame, text="Add", command=self.on_add_click, style="Toggle.TButton").pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Edit", command=self.on_edit_click).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Complete", command=self.on_complete_click).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Delete", command=self.on_delete_click).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Snooze", command=self.on_snooze_preset_click).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Analytics", command=self.on_analytics_click).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Sync", command=self.on_sync_click).pack(fill="x", pady=4)

        # Right content area: search and tree
        # Search bar
        frm_search = ttk.Frame(right, style="Modern.TFrame", padding=8)
        frm_search.pack(fill="x")
        ttk.Label(frm_search, text="Search:", style="Modern.TLabel").grid(row=0, column=0, sticky="w")
        self.entry_search = ttk.Entry(frm_search, width=40, style="Modern.TEntry")
        self.entry_search.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.entry_search.bind("<KeyRelease>", self.refresh_list)

        # Treeview
        self.cols = ("id", "title", "notes", "due_date", "priority", "status", "urgency", "due_status")
        cols = self.cols[:]
        # Create a container frame for the tree and its scrollbars
        tree_container = ttk.Frame(right)
        tree_container.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        # Horizontal and vertical scrollbars
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal")
        v_scroll = ttk.Scrollbar(tree_container, orient="vertical")

        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", selectmode="extended", style="Modern.Treeview")
        # Attach scroll commands
        self.tree.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        h_scroll.configure(command=self.tree.xview)
        v_scroll.configure(command=self.tree.yview)

        # Layout with grid so scrollbars align correctly
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew", columnspan=2)

        headings = [
            ("id", 60), ("title", 360), ("notes", 260), ("due_date", 110),
            ("priority", 100), ("status", 100), ("urgency", 80), ("due_status", 100)
        ]
        for c, w in headings:
            col_anchor = "w" if c == "title" else "center"
            heading_anchor = "center"
            self.tree.heading(c, text=c.replace("_", " ").title(), anchor=heading_anchor, command=lambda col=c: self.on_column_click(col))
            self.tree.column(c, width=w, anchor=col_anchor)
        # note: packed via grid in the tree_container

        # Row tags for styling (colors set via _apply_theme)
        self.tree.tag_configure("overdue", background="#ffcccc")
        self.tree.tag_configure("due_soon", background="#fff2cc")
        self.tree.tag_configure("completed", background="#ccffcc")
        self.tree.tag_configure("normal", background="")
        self.tree.tag_configure("urgent", background="#ffe6cc")

        # Bind double-click to quick snooze (example)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

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
                        # treat any past due date as just "Overdue" (no "Very Overdue" distinction)
                        due_status = "Overdue"      
                    elif status != "Completed" and (d - date.today()).days <= 3:
                        due_status = "Due Soon"
            except Exception:
                due_status = ""

            # decide tag
            tag = "normal"
            if due_status == "Overdue":
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
        # Support single or multiple selection: if multiple selected, use bulk complete flow
        task_ids = self._get_selected_task_ids()
        if not task_ids:
            messagebox.showinfo("Info", "Select a task to mark complete.")
            return
        if len(task_ids) > 1:
            # reuse existing bulk handler which includes confirmation
            self.on_bulk_complete()
            return
        # single selection
        try:
            self.tm.complete_task(task_ids[0])
        except Exception:
            try:
                # fallback for different TaskManager API
                self.tm.complete_task(int(task_ids[0]))
            except Exception:
                pass
        self.refresh_list()

    def on_delete_click(self):
        # Support single or multiple selection: if multiple selected, use bulk delete flow
        task_ids = self._get_selected_task_ids()
        if not task_ids:
            messagebox.showinfo("Info", "Select a task to delete.")
            return
        if len(task_ids) > 1:
            # reuse existing bulk handler which includes confirmation
            self.on_bulk_delete()
            return
        # single selection
        tid = task_ids[0]
        if not messagebox.askyesno("Confirm", f"Delete task id {tid}?"):
            return
        try:
            self.tm.delete_task(tid)
        except Exception:
            try:
                self.tm.delete_task(int(tid))
            except Exception:
                pass
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