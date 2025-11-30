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
        try:
            self.root.geometry("1000x640")
        except Exception:
            pass

        # State
        self.tm = TaskManager()
        self.sort_column = None
        self.sort_reverse = False
        self.current_theme = "light"  # default theme

        # Styling
        self.style = ttk.Style(self.root)
        try:
            # clam is a good neutral base that allows customizing heading bg
            self.style.theme_use("clam")
        except Exception:
            pass

        self._init_styles()
        self._build_ui()
        self._apply_theme(self.current_theme)
        self.refresh_list()

    def _init_styles(self):
        """Initialize ttk styles for a modern light/dark look (Windows 11 clean)."""
        default_font = ("Segoe UI", 10)
        semibold = ("Segoe UI Semibold", 10)
        header_font = ("Segoe UI Semibold", 12)

        # Frames & labels
        self.style.configure("Modern.TFrame", background="#f3f3f3")
        self.style.configure("Sidebar.TFrame", background="#f3f3f3")
        self.style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        self.style.configure("Header.TLabel", font=header_font, background="#f3f3f3")
        self.style.configure("SubHeader.TLabel", font=semibold, background="#f3f3f3")
        self.style.configure("Modern.TLabel", font=default_font, background="#f3f3f3")

        # Entries (flat)
        self.style.configure("Modern.TEntry",
                             font=default_font,
                             fieldbackground="#ffffff",
                             background="#ffffff",
                             relief="flat",
                             padding=6)

        # Combobox - theme-aware baseline (entry portion + fieldbackground)
        # Use a dedicated style name so we can update it from _apply_theme
        self.style.configure("Modern.TCombobox",
                             font=default_font,
                             fieldbackground="#ffffff",
                             background="#ffffff",
                             foreground="#000000",
                             padding=4)
        try:
            self.style.map("Modern.TCombobox",
                           fieldbackground=[("readonly", "#ffffff"), ("!disabled", "#ffffff")],
                           foreground=[("disabled", "#888888"), ("!disabled", "#000000")])
        except Exception:
            pass

        # Spinbox (ttk) - make a modern themed spinbox style
        # fieldbackground controls the edit field color
        try:
            self.style.configure("Modern.TSpinbox",
                                 font=default_font,
                                 fieldbackground="#ffffff",
                                 background="#ffffff",
                                 foreground="#000000",
                                 padding=4)
            self.style.map("Modern.TSpinbox",
                           fieldbackground=[("!disabled", "#ffffff"), ("disabled", "#f0f0f0")],
                           foreground=[("!disabled", "#000000"), ("disabled", "#888888")])
        except Exception:
            # older ttk themes / tk versions may raise — ignore gracefully
            pass

        # Buttons (neutral gray, flat)
        self.style.configure("Modern.TButton",
                             font=semibold,
                             background="#e6e6e6",
                             foreground="#000000",
                             relief="flat",
                             padding=(8, 6))
        self.style.map("Modern.TButton",
                       background=[("active", "#d4d4d4"), ("disabled", "#f0f0f0")],
                       relief=[("pressed", "flat")])

        # Small icon-ish button (baseline)
        self.style.configure("Icon.TButton",
                             font=("Segoe UI Semibold", 9),
                             padding=4,
                             relief="flat",
                             background="#e6e6e6",
                             foreground="#000000")
        self.style.map("Icon.TButton",
                       background=[("active", "#d4d4d4"), ("disabled", "#f0f0f0")],
                       foreground=[("disabled", "#888888"), ("!disabled", "#000000")])

        # Treeview styling
        self.style.configure("Modern.Treeview", font=default_font, rowheight=28, background="#ffffff", fieldbackground="#ffffff")
        self.style.configure("Modern.Treeview.Heading", font=semibold, background="#f3f3f3")
        try:
            # keep default layout but allow custom heading bg to show
            self.style.layout("Treeheading.Cell", self.style.layout("Treeheading.Cell"))
        except Exception:
            pass

        # Scrollbar styling (subtle)
        try:
            self.style.configure("Modern.Vertical.TScrollbar",
                                 troughcolor="#f3f3f3",
                                 background="#d0d0d0",
                                 arrowcolor="#3a3a3a",
                                 relief="flat")
            self.style.configure("Modern.Horizontal.TScrollbar",
                                 troughcolor="#f3f3f3",
                                 background="#d0d0d0",
                                 arrowcolor="#3a3a3a",
                                 relief="flat")
        except Exception:
            pass

    def _apply_theme(self, mode: str):
        """Apply light or dark colors. Keeps neutral gray buttons and slightly rounded visual."""
        if mode == "dark":
            root_bg = "#252526"
            sidebar_bg = "#252526"
            panel_bg = "#2d2d30"
            fg = "#ffffff"
            heading_bg = "#2b2b2b"
            tree_bg = "#252526"
            row_bg = "#2d2d30"
            button_bg = "#3a3a3a"
            button_active = "#4a4a4a"
            scrollbar_bg = "#4a4a4a"
            text_bg = "#2d2d30"
        else:
            root_bg = "#f3f3f3"
            sidebar_bg = "#f3f3f3"
            panel_bg = "#ffffff"
            fg = "#000000"
            heading_bg = "#f3f3f3"
            tree_bg = "#ffffff"
            row_bg = "#ffffff"
            button_bg = "#e6e6e6"
            button_active = "#d4d4d4"
            scrollbar_bg = "#d0d0d0"
            text_bg = "#ffffff"

        # Frames and labels
        self.style.configure("Modern.TFrame", background=root_bg)
        self.style.configure("Sidebar.TFrame", background=sidebar_bg)
        self.style.configure("Panel.TFrame", background=panel_bg)
        self.style.configure("Modern.TLabel", background=root_bg, foreground=fg)
        self.style.configure("Header.TLabel", background=root_bg, foreground=fg)
        self.style.configure("SubHeader.TLabel", background=text_bg, foreground=fg)

        # Entries
        self.style.configure("Modern.TEntry", fieldbackground=panel_bg, background=panel_bg, foreground=fg)

        # Combobox: update entry/field colours to match panel and text colour
        try:
            # prefer to set arrowcolor when available (Tk 8.6.x+ on many platforms)
            self.style.configure("Modern.TCombobox",
                                 fieldbackground=panel_bg,
                                 background=panel_bg,
                                 foreground=fg,
                                 arrowcolor=fg)
            self.style.map("Modern.TCombobox",
                           fieldbackground=[("readonly", panel_bg), ("!disabled", panel_bg)],
                           foreground=[("disabled", "#888888"), ("!disabled", fg)])
        except Exception:
            # older Tk / themes may not accept arrowcolor — ignore and keep other settings
            try:
                self.style.configure("Modern.TCombobox",
                                     fieldbackground=panel_bg,
                                     background=panel_bg,
                                     foreground=fg)
                self.style.map("Modern.TCombobox",
                               fieldbackground=[("readonly", panel_bg), ("!disabled", panel_bg)],
                               foreground=[("disabled", "#888888"), ("!disabled", fg)])
            except Exception:
                pass

        # Spinbox: update to match panel colors
        try:
            self.style.configure("Modern.TSpinbox",
                                 fieldbackground=panel_bg,
                                 background=panel_bg,
                                 foreground=fg)
            self.style.map("Modern.TSpinbox",
                           fieldbackground=[("!disabled", panel_bg), ("disabled", "#444444")],
                           foreground=[("!disabled", fg), ("disabled", "#888888")])
        except Exception:
            pass

        # Also make dropdown list match panel where possible (affects tk.Listbox used by the popdown)
        try:
            self.root.option_add("*Listbox.background", panel_bg)
            self.root.option_add("*Listbox.foreground", fg)
            self.root.option_add("*Listbox.selectBackground", button_active)
            self.root.option_add("*Listbox.selectForeground", fg)
        except Exception:
            pass

        # Buttons remain neutral gray but adapt to theme
        self.style.configure("Modern.TButton", background=button_bg, foreground=fg)
        self.style.map("Modern.TButton", background=[("active", button_active), ("disabled", "#f0f0f0")])

        # Icon button (calendar / small icons) — follow same theme colours
        try:
            self.style.configure("Icon.TButton", background=button_bg, foreground=fg)
            self.style.map("Icon.TButton",
                           background=[("active", button_active), ("disabled", "#444444")],
                           foreground=[("disabled", "#888888"), ("!disabled", fg)])
        except Exception:
            pass

        # Treeview colors
        self.style.configure("Modern.Treeview", background=tree_bg, fieldbackground=tree_bg, foreground=fg)
        self.style.configure("Modern.Treeview.Heading", background=heading_bg, foreground=fg)

        # Scrollbars
        try:
            self.style.configure("Modern.Vertical.TScrollbar", troughcolor = root_bg, background = scrollbar_bg, arrowcolor = fg)
            self.style.configure("Modern.Horizontal.TScrollbar", troughcolor = root_bg, background = scrollbar_bg, arrowcolor = fg)
            # also map active state for visual feedback
            self.style.map("Modern.Vertical.TScrollbar", background = [("active", button_active), ("!active", scrollbar_bg)])
            self.style.map("Modern.Horizontal.TScrollbar", background = [("active", button_active), ("!active", scrollbar_bg)])
        except Exception:
            pass

        # Tag colors for rows (soft pastels for light mode; richer for dark)
        if mode == "dark":
            self.tree_tag_colors = {
                "overdue": "#5a1515",
                "due_soon": "#5a4300",
                "completed": "#155a2a",
                "urgent": "#5a2b00",
                "normal": row_bg
            }
        else:
            self.tree_tag_colors = {
                "overdue": "#ffecec",
                "due_soon": "#fff8e6",
                "completed": "#e6ffed",
                "urgent": "#fff3e6",
                "normal": row_bg
            }

        try:
            self.root.configure(bg=root_bg)
        except Exception:
            pass

        # Update theme toggle tk.Button (icon + colors) if it exists
        try:
            if hasattr(self, "theme_icon_btn") and self.theme_icon_btn:
                icon_text = ("🌙" if getattr(self, "current_theme", "light") == "light" else "☀️")
                try:
                    self.theme_icon_btn.configure(text=icon_text, bg=button_bg, fg=fg, activebackground=button_active, bd=0, relief="flat")
                except Exception:
                    # some platforms may require different keys; ignore failures
                    try:
                        self.theme_icon_btn.configure(text=icon_text)
                    except Exception:
                        pass
        except Exception:
            pass

        # Reconfigure existing tree tags if tree exists
        if hasattr(self, "tree"):
            for tag, color in self.tree_tag_colors.items():
                try:
                    self.tree.tag_configure(tag, background=color)
                except Exception:
                    pass

        # Update text widgets theme-aware colors (notes/edit)
        try:
            if hasattr(self, "entry_notes"):
                self.entry_notes.config(bg=panel_bg, fg=fg, insertbackground=fg)
        except Exception:
            pass

        # Update paned sash and separators: ttk.Panedwindow has no direct style, tweak through widget config
        try:
            # change trough/background for the paned widget and sash color via option database where possible
            # On some themes this may have no visible effect; set the paned background and the separator color through the parent
            if hasattr(self, "paned"):
                try:
                    self.paned.configure(style="Modern.TFrame")
                except Exception:
                    pass
        except Exception:
            pass

    def _toggle_theme(self):
        # flip theme, reapply styles and refresh UI; also update the toggle icon immediately
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        # update icon text on the button (safe-guard if button exists)
        try:
            if hasattr(self, "theme_icon_btn") and self.theme_icon_btn:
                icon_text = ("🌙" if self.current_theme == "light" else "☀️")
                try:
                    self.theme_icon_btn.configure(text=icon_text)
                except Exception:
                    pass
        except Exception:
            pass

        self._apply_theme(self.current_theme)
        self.refresh_list()
        # update analytics theme if open
        try:
            if hasattr(self, "analytics_win") and self.analytics_win:
                updater = self.analytics_win.get("update_theme") if isinstance(self.analytics_win, dict) else None
                if callable(updater):
                    updater(self.current_theme)
        except Exception:
            pass

    def _build_ui(self):
        # Main container
        container = ttk.Frame(self.root, style="Modern.TFrame", padding=10)
        container.pack(fill="both", expand=True)

        # Paned window to separate left and right (keeps layout stable)
        # keep a reference so theme updates can tweak the sash/background
        self.paned = ttk.Panedwindow(container, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)

        # Left sidebar (you chose light gray)
        self.left = ttk.Frame(self.paned, style="Sidebar.TFrame", width=350)
        self.left.pack_propagate(False)
        self.paned.add(self.left, weight=0)

        # Right content area
        right = ttk.Frame(self.paned, style="Modern.TFrame")
        self.paned.add(right, weight=1)

        # Header (title) inside left
        header_container = ttk.Frame(self.left, style="Sidebar.TFrame")
        header_container.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Label(header_container, text="Smart To-Do List", style="Header.TLabel", anchor="w").pack(fill="x")

        # Theme toggle button (tk.Button for predictable bg)
        icon_text = ("🌙" if self.current_theme == "light" else "☀️")
        self.theme_icon_btn = tk.Button(self.root, text=icon_text, command=self._toggle_theme,
                                       bd=0, relief="flat")
        self.theme_icon_btn.place(relx=1.0, x=-40, y=35, anchor="ne")

        # Input frame inside left (panel look)
        inp_frame_outer = ttk.Frame(self.left, style="Panel.TFrame", padding=10)
        inp_frame_outer.pack(fill="both", expand=False, padx=12, pady=(6, 0))
        inp_frame_outer.columnconfigure(1, weight=1)

        # Task
        ttk.Label(inp_frame_outer, text="Task:", style="SubHeader.TLabel").grid(row=0, column=0, sticky="w")
        self.entry_title = ttk.Entry(inp_frame_outer, style="Modern.TEntry")
        self.entry_title.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=6)

        # Due
        ttk.Label(inp_frame_outer, text="Due (YYYY-MM-DD):", style="SubHeader.TLabel").grid(row=1, column=0, sticky="w")
        frm_due = ttk.Frame(inp_frame_outer, style="Panel.TFrame")
        frm_due.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=6)
        self.entry_due = ttk.Entry(frm_due, width=18, style="Modern.TEntry")
        self.entry_due.pack(side="left")
        ttk.Button(frm_due, text="📅", width=3, style="Icon.TButton", command=self.on_pick_due_date).pack(side="left", padx=(8, 0))

        # Priority
        ttk.Label(inp_frame_outer, text="Priority:", style="SubHeader.TLabel").grid(row=2, column=0, sticky="w")
        self.entry_priority = ttk.Combobox(inp_frame_outer, values=list(PRIORITY_LEVELS), width=18, style="Modern.TCombobox")
        self.entry_priority.set("Normal")
        self.entry_priority.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=6)

        # Notes (Text widget inside panel to give 'card' look)
        ttk.Label(inp_frame_outer, text="Notes:", style="SubHeader.TLabel").grid(row=3, column=0, sticky="nw", pady=(6, 0))
        notes_frame = ttk.Frame(inp_frame_outer, style="Panel.TFrame", padding=4)
        notes_frame.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(6, 0))
        self.entry_notes = tk.Text(notes_frame, height=6, bd=0, relief="flat", wrap="word")
        self.entry_notes.pack(fill="both", expand=True)
        # Ensure the text widget colours match the panel in _apply_theme

        # Action buttons (neutral gray) - slightly rounded feel via padding
        btn_frame = ttk.Frame(self.left, style="Sidebar.TFrame")
        btn_frame.pack(fill="x", padx=12, pady=(12, 12))
        ttk.Button(btn_frame, text="Add", command=self.on_add_click, style="Modern.TButton").pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="Edit", command=self.on_edit_click, style="Modern.TButton").pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="Complete", command=self.on_complete_click, style="Modern.TButton").pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="Delete", command=self.on_delete_click, style="Modern.TButton").pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="Snooze", command=self.on_snooze_preset_click, style="Modern.TButton").pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="Analytics", command=self.on_analytics_click, style="Modern.TButton").pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="Sync", command=self.on_sync_click, style="Modern.TButton").pack(fill="x", pady=6)

        # Right area: Search + Tree inside a white panel for card feel
        right_top = ttk.Frame(right, style="Panel.TFrame", padding=(10, 8))
        right_top.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Label(right_top, text="Search:", style="SubHeader.TLabel").grid(row=0, column=0, sticky="w")
        self.entry_search = ttk.Entry(right_top, width=40, style="Modern.TEntry")
        self.entry_search.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.entry_search.bind("<KeyRelease>", self.refresh_list)

        # Treeview container
        tree_container = ttk.Frame(right, style="Modern.TFrame")
        tree_container.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        # Scrollbars
        # Keep references to the scrollbars so we can reconfigure them when theme changes
        self.h_scroll = ttk.Scrollbar(tree_container, orient="horizontal", style="Modern.Horizontal.TScrollbar")
        self.v_scroll = ttk.Scrollbar(tree_container, orient="vertical", style="Modern.Vertical.TScrollbar")

        # remove id column from visible columns; we'll store task_id in the item's iid
        self.cols = ("title", "notes", "due_date", "priority", "status", "urgency", "due_status")
        cols = self.cols[:]
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", selectmode="extended", style="Modern.Treeview")
        self.tree.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        self.h_scroll.configure(command=self.tree.xview)
        self.v_scroll.configure(command=self.tree.yview)

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew", columnspan=2)

        # Adjust column widths now that 'id' is not visible
        headings = [
            ("title", 200), ("notes", 260), ("due_date", 110),
            ("priority", 100), ("status", 100), ("urgency", 80), ("due_status", 100)
        ]
        for c, w in headings:
            col_anchor = "w" if c == "title" else "center"
            heading_anchor = "center"
            # heading click sorts by column
            self.tree.heading(c, text=c.replace("_", " ").title(), anchor=heading_anchor,
                              command=lambda col=c: self.on_column_click(col))
            self.tree.column(c, width=w, anchor=col_anchor)

        # Row tags (colors applied in _apply_theme)
        self.tree.tag_configure("overdue", background="#ffcccc")
        self.tree.tag_configure("due_soon", background="#fff2cc")
        self.tree.tag_configure("completed", background="#ccffcc")
        self.tree.tag_configure("normal", background="")
        self.tree.tag_configure("urgent", background="#fff3e6")

        # Bind double click
        self.tree.bind("<Double-1>", self.on_tree_double_click)

    # -------------------------
    # Data and interactions
    # -------------------------
    def on_column_click(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_list()

    def refresh_list(self, event=None):
        for i in self.tree.get_children():
            self.tree.delete(i)

        search_term = (self.entry_search.get() or "").lower()
        tasks = getattr(self.tm, "tasks", [])[:] or []

        # Filter by search term across title/priority/status/notes
        filtered_tasks = [
            t for t in tasks if (
                search_term in (getattr(t, "title", "") or "").lower() or
                search_term in (getattr(t, "priority_level", "Normal") or "").lower() or
                search_term in (getattr(t, "status", "") or "").lower() or
                search_term in (getattr(t, "notes", "") or "").lower()
            )
        ] if search_term else tasks

        # Sorting
        if self.sort_column:
            try:
                if self.sort_column == "due_date":
                    filtered_tasks.sort(key=lambda t: t.due_date or "", reverse=self.sort_reverse)
                elif self.sort_column == "urgency":
                    filtered_tasks.sort(key=lambda t: self.tm.compute_urgency_score(t), reverse=self.sort_reverse)
                elif self.sort_column == "priority":
                    filtered_tasks.sort(key=lambda t: getattr(t, "priority_level", "Normal") or "", reverse=self.sort_reverse)
                elif self.sort_column == "status":
                    filtered_tasks.sort(key=lambda t: getattr(t, "status", "") or "", reverse=self.sort_reverse)
                elif self.sort_column == "title":
                    filtered_tasks.sort(key=lambda t: getattr(t, "title", "") or "", reverse=self.sort_reverse)
            except Exception:
                pass

        for t in filtered_tasks:
            tid = getattr(t, "task_id", None)
            title = getattr(t, "title", "") or ""
            notes = (getattr(t, "notes", "") or "").replace("\n", " ")[:150]
            due = getattr(t, "due_date", "") or ""
            priority = getattr(t, "priority_level", "Normal") or "Normal"
            status = getattr(t, "status", "") or ""
            urgency_score = 0.0
            try:
                urgency_score = self.tm.compute_urgency_score(t)
            except Exception:
                pass

            due_status = ""
            try:
                if getattr(t, "due_date", None):
                    d = datetime.fromisoformat(t.due_date).date()
                    if status != "Completed" and d < date.today():
                        due_status = "Overdue"
                    elif status != "Completed" and (d - date.today()).days <= 3:
                        due_status = "Due Soon"
            except Exception:
                due_status = ""

            tag = "normal"
            if due_status == "Overdue":
                tag = "overdue"
            elif due_status == "Due Soon":
                tag = "due_soon"
            if status == "Completed":
                tag = "completed"
            elif urgency_score >= 5.0 and tag == "normal":
                tag = "urgent"

            # values no longer include the id (id stored in iid)
            vals = (title, notes, due, priority, status, f"{urgency_score:.2f}", due_status)
            try:
                iid = str(tid) if tid is not None else None
                # if iid is None Treeview will auto-generate one; that's fine for unsaved tasks
                self.tree.insert("", "end", iid=iid, values=vals, tags=(tag,))
            except Exception:
                pass

    def on_add_click(self):
        title = (self.entry_title.get() or "").strip()
        due = (self.entry_due.get() or "").strip()
        priority = (self.entry_priority.get() or "Normal").strip() or "Normal"
        notes = (self.entry_notes.get("1.0", tk.END) or "").strip()

        if not title:
            self._themed_warning("Validation", "Task title is required.")
            return

        if due:
            try:
                datetime.fromisoformat(due)
            except Exception:
                self._themed_warning("Validation", "Due date must be YYYY-MM-DD or blank.")
                return

        try:
            task_obj = self.tm.add_task(title, due or None, priority, "Pending", notes=notes)
        except TypeError:
            task_obj = self.tm.add_task(title, due or None, priority, "Pending")
            try:
                if hasattr(self.tm, "tasks") and self.tm.tasks:
                    last = self.tm.tasks[-1]
                    setattr(last, "notes", notes)
            except Exception:
                pass
        except Exception:
            task_obj = self.tm.add_task(title, due or None, priority, "Pending")
            try:
                if hasattr(self.tm, "tasks") and self.tm.tasks:
                    last = self.tm.tasks[-1]
                    setattr(last, "notes", notes)
            except Exception:
                pass

        # clear inputs
        try:
            self.entry_title.delete(0, tk.END)
            self.entry_due.delete(0, tk.END)
            self.entry_priority.set("Normal")
            self.entry_notes.delete("1.0", tk.END)
        except Exception:
            pass
        self.refresh_list()

    def _get_selected_task_ids(self):
        sel = self.tree.selection()
        task_ids = []
        for item in sel:
            try:
                task_ids.append(int(item))
            except Exception:
                # ignore items without numeric iid
                continue
        return [tid for tid in task_ids if tid is not None]

    def _get_selected_task_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        iid = sel[0]
        try:
            return int(iid)
        except Exception:
            return None

    def _find_task_by_id(self, task_id):
        for t in getattr(self.tm, "tasks", []) or []:
            try:
                if getattr(t, "task_id", None) == task_id:
                    return t
            except Exception:
                continue
        return None

    def on_snooze_preset_click(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            self._themed_info("Info", "Select a task to snooze.")
            return

        snooze_win = tk.Toplevel(self.root)
        snooze_win.title("Snooze Task")
        snooze_win.transient(self.root)
        snooze_win.grab_set()
        self._center_popup(snooze_win, width=315, height=200, parent=self.root)

        container = ttk.Frame(snooze_win, style="Panel.TFrame")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # theme-aware panel colors
        panel_bg = self.style.lookup("Panel.TFrame", "background") or ("#ffffff" if self.current_theme == "light" else "#2d2d30")
        fg = self.style.lookup("Modern.TLabel", "foreground") or ("#000000" if self.current_theme == "light" else "#ffffff")

        # canvas must share the panel background so rows between buttons don't show system gray
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0, bg=panel_bg)
        vscroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview, style="Modern.Vertical.TScrollbar")
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # inner frame explicitly uses Panel.TFrame so it matches panel_bg
        inner = ttk.Frame(canvas, style="Panel.TFrame")
        canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_config(event):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.config(bg=panel_bg)
            except Exception:
                pass

        inner.bind("<Configure>", _on_inner_config)

        ttk.Label(inner, text="Snooze by:", style="SubHeader.TLabel", font=("Segoe UI", 10, "bold"), anchor="w").pack(pady=10, padx=6, fill="x")

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
                self._themed_info("Snoozed", f"Task snoozed by {days} day(s). New due: {res.due_date}")
                snooze_win.destroy()
                self.refresh_list()
            else:
                self._themed_warning("Snooze", "Failed to snooze task.")

        for label, days in presets:
            ttk.Button(inner, text=label, command=lambda d=days: snooze_by(d), style="Modern.TButton").pack(fill="x", padx=10, pady=4)

        ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=10, pady=10)
        ttk.Label(inner, text="Custom days:", style="SubHeader.TLabel", anchor="w").pack(pady=5, padx=10, fill="x")
        spin_days = SpinboxWithButtons(inner, from_=1, to=365, width=6, initial=1, bg=panel_bg, fg=fg, step=1)
        spin_days.pack(pady=5, padx=10, anchor="w")
        ttk.Button(inner, text="Apply Custom", command=lambda: snooze_by(int(spin_days.get())), style="Modern.TButton").pack(pady=10, padx=10)

        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def on_edit_click(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            self._themed_info("Info", "Select a task to edit.")
            return

        t = self._find_task_by_id(task_id)
        if not t:
            self._themed_warning("Edit", f"Task {task_id} not found in memory.")
            return

        edit_win = tk.Toplevel(self.root)
        task_title = getattr(t, "title", None) or str(task_id)
        edit_win.title(f"Edit Task '{task_title}'")
        edit_win.transient(self.root)
        edit_win.grab_set()
        self._center_popup(edit_win, width=520, height=320, parent=self.root)

        content = ttk.Frame(edit_win, style="Panel.TFrame", padding=10)
        content.pack(fill="both", expand=True)

        ttk.Label(content, text="Task:", style="SubHeader.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=6,)
        e_title = ttk.Entry(content, width=40, style="Modern.TEntry")
        e_title.grid(row=0, column=1, padx=6, pady=6)
        e_title.insert(0, getattr(t, "title", "") or "")

        ttk.Label(content, text="Due (YYYY-MM-DD):", style="SubHeader.TLabel").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        frm_due_edit = ttk.Frame(content, style="Panel.TFrame")
        frm_due_edit.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        e_due = ttk.Entry(frm_due_edit, width=20, style="Modern.TEntry")
        e_due.pack(side="left")
        e_due.insert(0, getattr(t, "due_date", "") or "")
        ttk.Button(frm_due_edit, text="📅", width=3, style="Icon.TButton", command=lambda: self._open_edit_date_picker(edit_win, e_due)).pack(side="left", padx=(8,0))

        ttk.Label(content, text="Priority:", style="SubHeader.TLabel").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        e_priority = ttk.Combobox(content, values=list(PRIORITY_LEVELS), width=18, style="Modern.TCombobox")
        e_priority.grid(row=2, column=1, padx=6, pady=6)
        e_priority.set(getattr(t, "priority_level", "Normal") or "Normal")

        ttk.Label(content, text="Status:", style="SubHeader.TLabel").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        e_status = ttk.Combobox(content, values=["Pending", "Completed"], width=18, style="Modern.TCombobox")
        e_status.grid(row=3, column=1, padx=6, pady=6)
        e_status.set(getattr(t, "status", "Pending") or "Pending")

        ttk.Label(content, text="Notes:", style="SubHeader.TLabel").grid(row=4, column=0, sticky="nw", padx=6, pady=6)
        e_notes_frame = ttk.Frame(content, style="Panel.TFrame", padding=4)
        e_notes_frame.grid(row=4, column=1, padx=6, pady=6, sticky="ew")
        e_notes = tk.Text(e_notes_frame, width=40, height=4, bd=0, relief="flat", wrap="word")
        e_notes.pack(fill="both", expand=True)
        e_notes.insert("1.0", getattr(t, "notes", "") or "")

        # Make Text match theme
        try:
            if getattr(self, "current_theme", "light") == "dark":
                _panel_bg = "#2d2d30"
                _fg = "#ffffff"
            else:
                _panel_bg = "#ffffff"
                _fg = "#000000"
            e_notes.config(bg=_panel_bg, fg=_fg, insertbackground=_fg)
        except Exception:
            pass

        def save_changes(event=None):
            new_title = e_title.get().strip()
            new_due = e_due.get().strip()
            new_prio = e_priority.get().strip() or "Normal"
            new_status = e_status.get().strip() or "Pending"
            new_notes = e_notes.get("1.0", tk.END).strip()

            if not new_title:
                self._themed_warning("Validation", "Task title is required.", parent=edit_win)
                return
            if new_due:
                try:
                    datetime.fromisoformat(new_due)
                except Exception:
                    self._themed_warning("Validation", "Due date must be YYYY-MM-DD or blank.", parent=edit_win)
                    return

            try:
                if hasattr(self.tm, "update_task"):
                    try:
                        self.tm.update_task(task_id, title=new_title, due_date=new_due or None, priority=new_prio, status=new_status)
                    except TypeError:
                        self.tm.update_task(task_id, title=new_title, due_date=new_due or None, priority_level=new_prio, status=new_status)
                else:
                    setattr(t, "title", new_title)
                    setattr(t, "due_date", new_due or None)
                    setattr(t, "priority_level", new_prio)
                    setattr(t, "status", new_status)
                setattr(t, "notes", new_notes)
                setattr(t, "priority_level", new_prio)
            except Exception as ex:
                self._themed_error("Edit Error", f"Failed to update task: {ex}", parent=edit_win)
                return

            edit_win.grab_release()
            edit_win.destroy()
            self.refresh_list()

        btn_frame = ttk.Frame(content, style="Panel.TFrame")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(8,12))

        # Keep buttons on the panel background and center them
        inner_btns = ttk.Frame(btn_frame, style="Panel.TFrame")
        inner_btns.pack(anchor="center")

        ttk.Button(inner_btns, text="Save", command=save_changes, style="Modern.TButton").pack(side="left", padx=(0,6))
        ttk.Button(inner_btns, text="Cancel", command=lambda: (edit_win.grab_release(), edit_win.destroy()), style="Modern.TButton").pack(side="left")

        edit_win.bind("<Return>", save_changes)
        e_title.focus_set()

    def on_complete_click(self):
        task_ids = self._get_selected_task_ids()
        if not task_ids:
            self._themed_info("Info", "Select a task to mark complete.")
            return
        if len(task_ids) > 1:
            self.on_bulk_complete()
            return
        try:
            self.tm.complete_task(task_ids[0])
        except Exception:
            try:
                self.tm.complete_task(int(task_ids[0]))
            except Exception:
                pass
        self.refresh_list()

    def on_delete_click(self):
        task_ids = self._get_selected_task_ids()
        if not task_ids:
            self._themed_info("Info", "Select a task to delete.")
            return
        if len(task_ids) > 1:
            self.on_bulk_delete()
            return
        tid = task_ids[0]
        task_obj = self._find_task_by_id(tid)
        task_title = getattr(task_obj, "title", None) or str(tid)
        if not self._themed_askyesno("Confirm", f"Delete task '{task_title}'?"):
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
            self._themed_info("Info", "Select tasks to mark complete.")
            return
        if not self._themed_askyesno("Confirm", f"Mark {len(task_ids)} task(s) as complete?"):
            return
        for tid in task_ids:
            self.tm.complete_task(tid)
        self.refresh_list()

    def on_bulk_delete(self):
        task_ids = self._get_selected_task_ids()
        if not task_ids:
            self._themed_info("Info", "Select tasks to delete.")
            return
        if not self._themed_askyesno("Confirm", f"Delete {len(task_ids)} task(s)?"):
            return
        for tid in task_ids:
            self.tm.delete_task(tid)
        self.refresh_list()

    def on_double_click(self, _event):
        task_id = self._get_selected_task_id()
        if not task_id:
            return
        res = self.tm.snooze_task(task_id, days=1)
        if res:
            self._themed_info("Quick Snooze", f"Task {task_id} snoozed to {res.due_date}")
            self.refresh_list()

    def on_sync_click(self):
        summary = self.tm.sync_with_remote(prefer_local=True)
        self._themed_info("Sync complete", f"Pushed: {summary.get('pushed',0)}\nPulled: {summary.get('pulled',0)}\nUpdated: {summary.get('updated',0)}")
        self.refresh_list()

    def on_analytics_click(self):
        try:
            try:
                self.analytics_win = show_analytics_tk(self.tm, parent=self.root, days_back=14, theme=self.current_theme)
            except Exception:
                show_analytics_tk(self.tm, parent=self.root, days_back=14, theme=self.current_theme)
        except Exception as ex:
            self._themed_error("Analytics Error", f"Failed to open analytics: {ex}")

    def on_pick_due_date(self):
        date_win = tk.Toplevel(self.root)
        date_win.title("Pick Due Date")
        date_win.transient(self.root)
        date_win.grab_set()
        self._center_popup(date_win, width=300, height=240, parent=self.root)

        # theme-aware panel colors
        panel_bg = self.style.lookup("Panel.TFrame", "background") or ("#ffffff" if self.current_theme == "light" else "#2d2d30")
        fg = self.style.lookup("Modern.TLabel", "foreground") or ("#000000" if self.current_theme == "light" else "#ffffff")
        button_active = "#d4d4d4" if self.current_theme == "light" else "#4a4a4a"

        # set background of the Toplevel to the panel color so non-ttk areas match the theme
        try:
            date_win.configure(bg=panel_bg)
        except Exception:
            pass

        # Use a themed container so ttk widgets inherit the correct look and spacing
        container = ttk.Frame(date_win, style="Panel.TFrame", padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        date_win.grid_rowconfigure(0, weight=1)
        date_win.grid_columnconfigure(0, weight=1)

        ttk.Label(container, text="Year:", style="SubHeader.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        spin_year = SpinboxWithButtons(container, from_=2024, to=2030, width=6, initial=date.today().year, bg=panel_bg, fg=fg)
        spin_year.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(container, text="Month:", style="SubHeader.TLabel").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        spin_month = SpinboxWithButtons(container, from_=1, to=12, width=4, initial=date.today().month, bg=panel_bg, fg=fg)
        spin_month.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(container, text="Day:", style="SubHeader.TLabel").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        spin_day = SpinboxWithButtons(container, from_=1, to=31, width=4, initial=date.today().day, bg=panel_bg, fg=fg)
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
                self._themed_error("Date Error", f"Invalid date: {ex}", parent=date_win)

        btn = ttk.Button(container, text="Apply", command=apply_date, style="Modern.TButton")
        btn.grid(row=3, column=0, columnspan=2, pady=12)

    def on_tree_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        col = self.tree.identify_column(event.x)
        sel = self.tree.selection()
        if not sel:
            return
        try:
            col_index = int(col.replace("#", "")) - 1
            col_name = self.cols[col_index]
        except Exception:
            col_name = None

        task_id = self._get_selected_task_id()
        if not task_id:
            return
        if col_name == "status":
            self.tm.complete_task(task_id)
            self.refresh_list()
            return

        res = self.tm.snooze_task(task_id, days=1)
        if res:
            self._themed_info("Quick Snooze", f"Task {task_id} snoozed to {res.due_date}")
            self.refresh_list()

    def _open_edit_date_picker(self, parent_win, entry_widget):
        date_win = tk.Toplevel(parent_win)
        date_win.title("Pick Due Date")
        date_win.transient(parent_win)
        date_win.grab_set()
        self._center_popup(date_win, width=300, height=240, parent=parent_win)

        # theme-aware panel colors
        panel_bg = self.style.lookup("Panel.TFrame", "background") or ("#ffffff" if self.current_theme == "light" else "#2d2d30")
        fg = self.style.lookup("Modern.TLabel", "foreground") or ("#000000" if self.current_theme == "light" else "#ffffff")

        try:
            date_win.configure(bg=panel_bg)
        except Exception:
            pass

        container = ttk.Frame(date_win, style="Panel.TFrame", padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        date_win.grid_rowconfigure(0, weight=1)
        date_win.grid_columnconfigure(0, weight=1)

        ttk.Label(container, text="Year:", style="SubHeader.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        spin_year = SpinboxWithButtons(container, from_=2024, to=2030, width=6, initial=date.today().year, bg=panel_bg, fg=fg)
        spin_year.grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(container, text="Month:", style="SubHeader.TLabel").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        spin_month = SpinboxWithButtons(container, from_=1, to=12, width=4, initial=date.today().month, bg=panel_bg, fg=fg)
        spin_month.grid(row=1, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(container, text="Day:", style="SubHeader.TLabel").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        spin_day = SpinboxWithButtons(container, from_=1, to=31, width=4, initial=date.today().day, bg=panel_bg, fg=fg)
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
                self._themed_error("Date Error", f"Invalid date: {ex}", parent=date_win)

        ttk.Button(container, text="Apply", command=apply_date, style="Modern.TButton").grid(row=3, column=0, columnspan=2, pady=12)

    def _center_popup(self, popup: tk.Toplevel, width: int = None, height: int = None, parent: tk.Misc = None):
        parent = parent or self.root
        try:
            parent.update_idletasks()
            popup.update_idletasks()
            w = width or popup.winfo_reqwidth()
            h = height or popup.winfo_reqheight()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 2)
            popup.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            try:
                popup.geometry("+100+100")
            except Exception:
                pass

    def _themed_message(self, title: str, message: str, kind: str = "info", parent: tk.Misc = None) -> bool:
        parent = parent or self.root
        panel_bg = self.style.lookup("Panel.TFrame", "background") or ("#ffffff" if self.current_theme == "light" else "#2d2d30")
        fg = self.style.lookup("Modern.TLabel", "foreground") or ("#000000" if self.current_theme == "light" else "#ffffff")

        dlg = tk.Toplevel(parent)
        dlg.title(title)
        dlg.transient(parent)
        dlg.grab_set()
        self._center_popup(dlg, width=420, height=140, parent=parent)
        try:
            dlg.configure(bg=panel_bg)
        except Exception:
            pass

        cont = ttk.Frame(dlg, style="Panel.TFrame", padding=(12, 10))
        cont.pack(fill="both", expand=True)

        # Title + icon row
        try:
            header_font = self.style.lookup("Header.TLabel", "font") or ("Segoe UI Semibold", 12)
        except Exception:
            header_font = ("Segoe UI Semibold", 12)
        # use tk.Label so we can force the background color to match the panel
        lbl = tk.Label(cont, text=title, bg=panel_bg, fg=fg, font=header_font, anchor="w")
        lbl.grid(row=0, column=0, sticky="w", padx=2, pady=(0,6), columnspan=2)

        # Message (wrap)
        msg = tk.Label(cont, text=message, bg=panel_bg, fg=fg, justify="left", wraplength=380)
        msg.grid(row=1, column=0, columnspan=2, sticky="w", padx=2, pady=(0,12))

        result = {"value": None}

        def _on_ok():
            result["value"] = True
            try:
                dlg.grab_release()
            except Exception:
                pass
            dlg.destroy()

        def _on_no():
            result["value"] = False
            try:
                dlg.grab_release()
            except Exception:
                pass
            dlg.destroy()

        # Buttons
        if kind == "ask":
            b_yes = ttk.Button(cont, text="Yes", command=_on_ok, style="Modern.TButton")
            b_no = ttk.Button(cont, text="No", command=_on_no, style="Modern.TButton")
            b_yes.grid(row=2, column=0, sticky="e", padx=(0,6))
            b_no.grid(row=2, column=1, sticky="w")
            b_yes.focus_set()
        else:
            # single OK button
            b_ok = ttk.Button(cont, text="OK", command=_on_ok, style="Modern.TButton")
            b_ok.grid(row=2, column=0, columnspan=2)
            b_ok.focus_set()

        # Make sure controls are placed nicely
        cont.grid_columnconfigure(0, weight=1)
        cont.grid_columnconfigure(1, weight=0)

        parent.wait_window(dlg)
        return result["value"]

    # convenience wrappers
    def _themed_info(self, title: str, message: str, parent: tk.Misc = None):
        self._themed_message(title, message, kind="info", parent=parent)

    def _themed_warning(self, title: str, message: str, parent: tk.Misc = None):
        self._themed_message(title, message, kind="warning", parent=parent)

    def _themed_error(self, title: str, message: str, parent: tk.Misc = None):
        self._themed_message(title, message, kind="error", parent=parent)

    def _themed_askyesno(self, title: str, message: str, parent: tk.Misc = None) -> bool:
        return bool(self._themed_message(title, message, kind="ask", parent=parent))


# small custom spinbox that uses two arrow buttons so arrow color can follow theme
class SpinboxWithButtons(tk.Frame):
    def __init__(self, parent, from_=0, to=100, width=8, initial=None, bg=None, fg=None, step=1, **kw):
        # parent: parent widget
        # from_, to: numeric bounds
        # width: entry character width
        # bg, fg: colors to use for entry and arrow buttons
        super().__init__(parent, bg=bg)
        self._from = from_
        self._to = to
        self._step = step
        self._bg = bg or self.cget("bg")
        self._fg = fg or "#000000"

        # entry (styled to match your panel)
        self.entry = tk.Entry(self, width=width, bd=0, relief="flat",
                              justify="center", bg=self._bg, fg=self._fg, insertbackground=self._fg)
        self.entry.pack(side="left", fill="x", expand=True)

        # compact vertical button column
        btn_col = tk.Frame(self, bg=self._bg)
        btn_col.pack(side="right", fill="y")

        # Up / Down buttons use unicode arrows so color follows fg
        self._btn_up = tk.Button(btn_col, text="▲", bd=0, relief="flat",
                                 bg=self._bg, fg=self._fg, activebackground=self._bg,
                                 command=self._on_up)
        self._btn_up.pack(side="top", fill="x")
        self._btn_down = tk.Button(btn_col, text="▼", bd=0, relief="flat",
                                   bg=self._bg, fg=self._fg, activebackground=self._bg,
                                   command=self._on_down)
        self._btn_down.pack(side="top", fill="x")

        if initial is None:
            initial = from_ if from_ is not None else 0
        self.set(initial)

    def _parse(self):
        try:
            v = int(self.entry.get())
        except Exception:
            try:
                v = int(float(self.entry.get()))
            except Exception:
                v = self._from if self._from is not None else 0
        return v

    def _on_up(self):
        v = self._parse() + self._step
        if self._to is None or v <= self._to:
            self.set(v)

    def _on_down(self):
        v = self._parse() - self._step
        if self._from is None or v >= self._from:
            self.set(v)

    # API compatibility helpers
    def get(self):
        return self.entry.get()

    def set(self, val):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(val))

    # allow updating colors when theme changes
    def configure_colors(self, bg, fg):
        self._bg = bg
        self._fg = fg
        self.configure(bg=bg)
        self.entry.configure(bg=bg, fg=fg, insertbackground=fg)
        for b in (self._btn_up, self._btn_down):
            b.configure(bg=bg, fg=fg, activebackground=bg)


def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
