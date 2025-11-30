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

def create_analytics_figure(db_manager: Any, days_back: int = 14, theme: str = 'light') -> Figure:
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

    # theme-aware figure
    fig_bg = '#1e1e1e' if theme == 'dark' else '#ffffff'
    text_color = '#ffffff' if theme == 'dark' else '#000000'
    fig = Figure(figsize=(10, 6), tight_layout=True)
    fig.patch.set_facecolor(fig_bg)

    ax_top = fig.add_subplot(2, 1, 1)
    # set axis facecolor and text color
    ax_top.set_facecolor(fig_bg)
    ax_top.tick_params(colors=text_color)
    for spine in ax_top.spines.values():
        spine.set_color(text_color)

    if values.size:
        bar_color = '#4c72b0' if theme == 'light' else '#6fa8ff'
        line_color = '#dd8452' if theme == 'light' else '#ffb78f'
        ax_top.bar(x, values, color=bar_color, alpha=0.85, label="Completed per day")
        ax_top.plot(x, values, color=line_color, marker="o", label="Trend")
        ax_top.set_xticks(x)
        ax_top.set_xticklabels(xlabels, rotation=45, ha="right")
    else:
        ax_top.text(0.5, 0.5, "No completion data available", ha="center", va="center")
        ax_top.set_xticks([])
    ax_top.set_ylabel("Tasks Completed", color=text_color)
    ax_top.set_title(f"Tasks Completed (last {days_back} days)", color=text_color)
    legend = ax_top.legend(loc="upper left", facecolor=fig_bg)
    try:
        for t in legend.get_texts():
            t.set_color(text_color)
        legend.get_frame().set_edgecolor(text_color)
    except Exception:
        pass

    ax_pie = fig.add_subplot(2, 2, 3)
    ax_pie.set_facecolor(fig_bg)
    ax_pie.tick_params(colors=text_color)
    for spine in ax_pie.spines.values():
        spine.set_color(text_color)

    labels = list(prio_dist.keys()) or ["No Data"]
    sizes = list(prio_dist.values()) or [1]
    if sum(sizes) == 0:
        ax_pie.text(0.5, 0.5, "No priority data", ha="center", va="center", color=text_color)
    else:
        # capture pie chart text objects so we can style them for the theme
        patches, txts, autotexts = ax_pie.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
        try:
            for t in txts:
                t.set_color(text_color)
            for at in autotexts:
                at.set_color(text_color)
        except Exception:
            pass
    ax_pie.set_title("Priority Distribution", color=text_color)

    ax_stats = fig.add_subplot(2, 2, 4)
    ax_stats.set_facecolor(fig_bg)
    ax_stats.tick_params(colors=text_color)
    for spine in ax_stats.spines.values():
        spine.set_color(text_color)

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
    ax_stats.text(0.02, 0.5, summary_text, fontsize=11, va="center", color=text_color)
    ax_stats.axis("off")
    ax_stats.set_title("Summary Stats", color=text_color)

    return fig

def show_analytics_tk(db_manager: Any, parent: Optional[tk.Misc] = None, days_back: int = 14, theme: str = 'light') -> dict:
    own_root = False
    if parent is None:
        root = tk.Tk()
        own_root = True
    else:
        root = tk.Toplevel(parent)

    root.title("Productivity Analytics")
    root.geometry("900x600")
    # apply theme to the toplevel
    bg = '#1e1e1e' if theme == 'dark' else '#ffffff'
    fg = '#ffffff' if theme == 'dark' else '#000000'
    try:
        root.configure(bg=bg)
    except Exception:
        pass

    fig = create_analytics_figure(db_manager, days_back=days_back, theme=theme)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill="both", expand=True)

    # use tk.Frame for easier bg control
    btn_frame = tk.Frame(root, bg=bg, padx=6, pady=6)
    btn_frame.pack(fill="x")
    close_btn = tk.Button(btn_frame, text="Close", command=(root.destroy if own_root else root.destroy), bg=bg, fg=fg, bd=0)
    close_btn.pack(side="right", padx=8, pady=6)

    # provide an updater so caller can change theme live
    def update_theme(new_theme: str):
        if not getattr(root, 'winfo_exists', lambda: False)():
            return
        new_bg = '#1e1e1e' if new_theme == 'dark' else '#ffffff'
        new_fg = '#ffffff' if new_theme == 'dark' else '#000000'
        try:
            root.configure(bg=new_bg)
        except Exception:
            pass
        try:
            # recreate figure with new theme and swap into canvas
            new_fig = create_analytics_figure(db_manager, days_back=days_back, theme=new_theme)
            canvas.figure = new_fig
            canvas.draw()
        except Exception:
            pass
        try:
            btn_frame.config(bg=new_bg)
            close_btn.config(bg=new_bg, fg=new_fg)
        except Exception:
            pass

    # ensure update_theme is available to caller
    return {"root": root, "canvas": canvas, "update_theme": update_theme}

if __name__ == "__main__":  # quick manual test (uses DatabaseManager if available)
    try:
        from database_manager import DatabaseManager  # type: ignore
        db = DatabaseManager()
        show_analytics_tk(db)
        tk.mainloop()
    except Exception as ex:
        print("Failed to open analytics UI:", ex)