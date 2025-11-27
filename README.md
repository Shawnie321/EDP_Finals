✅ Todo Database (Python + Supabase)

A simple Python project that connects to a Supabase PostgreSQL database to perform full CRUD operations for tasks.



🧱 Setup Steps

1. Clone this repo

git clone https://github.com/Shawnie321/EDP_Finals.git

cd todo-supabase-python

(shawn-update)
Search / filter bar: added entry_search and filtering by title, priority, status, notes.
Column sorting: added sort_column/sort_reverse and clicking headings to sort (on_column_click).
Multi-select + bulk actions: switched Treeview to selectmode="extended"; added _get_selected_task_ids, on_bulk_complete, on_bulk_delete.
Inline & edit improvements:
Double-click behavior extended to target column names (on_tree_double_click) and toggle status / quick snooze.
Edit dialog: added inline date picker button that opens a scoped date picker (_open_edit_date_picker).
Date pickers:
Main add area: on_pick_due_date date picker next to due entry.
Edit dialog: small calendar button that opens _open_edit_date_picker.
Snooze presets: added on_snooze_preset_click with common durations + custom.
Notes / task description:
Added Notes Text in main add area (entry_notes) so user can provide notes at task creation.
Added Notes column to Treeview (short preview), included notes in edit dialog and in add/edit logic.
Attempt to pass notes to TaskManager.add_task when supported, otherwise fallback to set in-memory task.notes.
Edit priority bug fix: update_task call tries both "priority" and "priority_level" parameter names; also ensures in-memory attribute priority_level is set so "Critical" and other levels persist.
Due-status & styling:
Added more granular due_status: "Very Overdue", "Overdue", "Due Soon".
Added stronger row tag colors (very_overdue red, overdue light-red, due_soon orange, urgent yellow, completed green).
