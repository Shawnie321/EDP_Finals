"""
analytics.py

Build Matplotlib charts from either a DatabaseManager or TaskManager.
The functions will:
 - prefer `get_completed_counts_per_day` / `get_priority_distribution` when available,
 - otherwise compute counts from `task_manager.tasks`.
"""
from typing import Dict, Any, Optional
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import tkinter as tk
from tkinter import ttk
from datetime import datetime

def _get_counts_and_priority(db_like, days_back: int = 14):
    # Completed counts per day
    if hasattr(db_like, "get_completed_counts_per_day"):
        counts = db_like.get_completed_counts_per_day(days_back=days_back) or {}
    else:
        # assume TaskManager-like with .tasks
        counts_map = {}
        if hasattr(db_like, "tasks"):
            from collections import defaultdict
            dd = defaultdict(int)
            for t in getattr(db_like, "tasks", []):
                try:
                    # only count completed items
                    if getattr(t, "status", "") != "Completed":
                        continue
                    # prefer a completion timestamp then updated_at then due_date
                    ts = getattr(t, "completed_at", None) or getattr(t, "updated_at", None) or getattr(t, "due_date", None)
                    if not ts:
                        continue
                    day = ts.split("T")[0] if isinstance(ts, str) and "T" in ts else str(ts)
                    dd[day] += 1
                except Exception:
                    continue
            counts = dict(dd)
        else:
            counts = {}

    # Priority distribution
    if hasattr(db_like, "get_priority_distribution"):
        prio = db_like.get_priority_distribution() or {}
    else:
        # compute from tasks
        from collections import Counter
        prio = Counter()
        if hasattr(db_like, "tasks"):
            for t in getattr(db_like, "tasks", []):
                p = getattr(t, "priority_level", None) or getattr(t, "priority", None) or "Normal"
                prio[p] += 1
        prio = dict(prio)
    return counts, prio

def create_analytics_figure(db_manager: Any, days_back: int = 14) -> Figure:
    """
    Build a matplotlib Figure:
     - top: bar + line (tasks completed per day)
     - bottom-left: pie chart (priority distribution)
     - bottom-right: summary stats
    Accepts DatabaseManager or TaskManager.
    """
    counts, prio_dist = _get_counts_and_priority(db_manager, days_back=days_back)

    dates = sorted(counts.keys())
    if dates:
        values = np.array([counts[d] for d in dates], dtype=int)
        x = np.arange(len(dates))
        xlabels = [d[5:] if len(d) >= 10 else d for d in dates]
    else:
        values = np.array([], dtype=int)
        x = np.array([], dtype=int)
        xlabels = []

    fig = Figure(figsize=(10, 6), tight_layout=True)

    ax_top = fig.add_subplot(2, 1, 1)
    if values.size:
        ax_top.bar(x, values, color="#4c72b0", alpha=0.85, label="Completed per day")
        ax_top.plot(x, values, color="#dd8452", marker="o", label="Trend")
        ax_top.set_xticks(x)
        ax_top.set_xticklabels(xlabels, rotation=45, ha="right")
    else:
        ax_top.text(0.5, 0.5, "No completion data available", ha="center", va="center")
        ax_top.set_xticks([])
    ax_top.set_ylabel("Tasks Completed")
    ax_top.set_title(f"Tasks Completed (last {days_back} days)")
    ax_top.legend(loc="upper left")

    ax_pie = fig.add_subplot(2, 2, 3)
    labels = list(prio_dist.keys()) or ["No Data"]
    sizes = list(prio_dist.values()) or [1]
    if sum(sizes) == 0:
        ax_pie.text(0.5, 0.5, "No priority data", ha="center", va="center")
    else:
        ax_pie.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
    ax_pie.set_title("Priority Distribution")

    ax_stats = fig.add_subplot(2, 2, 4)
    if values.size:
        mean = float(np.mean(values))
        median = float(np.median(values))
        std = float(np.std(values, ddof=0))
        total = int(values.sum())
        summary_text = (
            f"Mean: {mean:.2f}\n"
            f"Median: {median:.2f}\n"
            f"Std Dev: {std:.2f}\n"
            f"Total Completed: {total}"
        )
    else:
        summary_text = "No completion data available"
    ax_stats.text(0.02, 0.5, summary_text, fontsize=11, va="center")
    ax_stats.axis("off")
    ax_stats.set_title("Summary Stats")

    return fig

def show_analytics_tk(db_manager: Any, parent: Optional[tk.Misc] = None, days_back: int = 14) -> None:
    """
    Open a Tk Toplevel (or root if parent is None) and embed the analytics Figure.
    Accepts TaskManager or DatabaseManager.
    """
    own_root = False
    if parent is None:
        root = tk.Tk()
        own_root = True
    else:
        root = tk.Toplevel(parent)

    root.title("Productivity Analytics")
    root.geometry("900x600")

    fig = create_analytics_figure(db_manager, days_back=days_back)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    btn_frame = ttk.Frame(root, padding=6)
    btn_frame.pack(fill="x")
    ttk.Button(btn_frame, text="Close", command=(root.destroy if own_root else root.destroy)).pack(side="right", padx=8, pady=6)

if __name__ == "__main__":  # quick manual test (uses DatabaseManager if available)
    try:
        from database_manager import DatabaseManager  # type: ignore
        db = DatabaseManager()
        show_analytics_tk(db)
        tk.mainloop()
    except Exception as ex:
        print("Failed to open analytics UI:", ex)