from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import json
import os
from datetime import datetime, date, timedelta

from database_manager import DatabaseManager

TASKS_JSON = "tasks.json"
PRIORITY_LEVELS = ("Low", "Normal", "High")
PRIORITY_WEIGHT = {"Low": 1, "Normal": 2, "High": 3}


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _normalize_priority(p: Optional[str]) -> str:
    if not p:
        return "Normal"
    p = str(p).strip().title()
    if p not in PRIORITY_LEVELS:
        # allow synonyms like "critical", "high", etc.
        for lvl in PRIORITY_LEVELS:
            if lvl.lower() == p.lower():
                return lvl
        return "Normal"
    return p


@dataclass
class Task:
    task_id: Optional[int]
    title: str
    due_date: Optional[str] = None  # ISO YYYY-MM-DD or None
    status: str = "Pending"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.task_id,
            "title": self.title,
            "due_date": self.due_date,
            "priority": None,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Task":
        return cls(
            task_id=d.get("id"),
            title=d.get("title", ""),
            due_date=d.get("due_date"),
            status=d.get("status", "Pending"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )


@dataclass
class PriorityTask(Task):
    priority_level: str = "Normal"

    def to_dict(self) -> Dict[str, Any]:
        base = {
            "id": self.task_id,
            "title": self.title,
            "due_date": self.due_date,
            "priority": self.priority_level,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        return base

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PriorityTask":
        return cls(
            task_id=d.get("id"),
            title=d.get("title", ""),
            due_date=d.get("due_date"),
            status=d.get("status", "Pending"),
            priority_level=_normalize_priority(d.get("priority") or d.get("priority_level")),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )


class TaskManager:
    """
    In-memory manager for Task / PriorityTask objects with JSON serialization and
    optional Supabase persistence via DatabaseManager.

    Added features:
     - normalized priority levels and weights
     - created_at / updated_at timestamps
     - helpers: set_priority, get_overdue_tasks, get_tasks_by_priority,
       upcoming_deadlines, snooze_task, urgency scoring and sorting
     - sync_with_remote updated to handle priority and timestamps
    """

    def __init__(self, db: Optional[DatabaseManager] = None, json_file: str = TASKS_JSON):
        self.db = db or DatabaseManager()
        self.json_file = json_file
        self.tasks: List[PriorityTask] = []
        # load initial data (prefers DB if available)
        self.load()

    # -----------------------
    # Loading / Saving
    # -----------------------
    def load(self) -> None:
        """
        Load tasks from Supabase if available; otherwise load from JSON file.
        """
        try:
            if getattr(self.db, "supabase", None):
                rows = self.db.get_all_tasks() or []
                self.tasks = [PriorityTask.from_dict(r) for r in rows]
            else:
                self.tasks = self._load_json_tasks()
        except Exception:
            # on any failure fallback to JSON
            self.tasks = self._load_json_tasks()

    def _load_json_tasks(self) -> List[PriorityTask]:
        if not os.path.exists(self.json_file):
            return []
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return [PriorityTask.from_dict(r) for r in raw]
        except Exception:
            return []

    def save_json(self) -> None:
        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in self.tasks], f, indent=2, ensure_ascii=False)
        except Exception as ex:
            print("❗ Failed to save tasks JSON:", ex)

    # -----------------------
    # CRUD operations
    # -----------------------
    def _next_local_id(self) -> int:
        return max((t.task_id or 0 for t in self.tasks), default=0) + 1

    def add_task(self, title: str, due_date: Optional[str] = None, priority: str = "Normal", status: str = "Pending") -> PriorityTask:
        """
        Add a task. Sets created_at/updated_at and normalized priority.
        """
        now = _now_iso()
        priority_n = _normalize_priority(priority)
        if getattr(self.db, "supabase", None):
            resp = self.db.add_task_to_db(title, due_date, priority_n, status)
            row = None
            if isinstance(resp, list) and len(resp):
                row = resp[0]
            elif isinstance(resp, dict):
                row = resp
            if row:
                # ensure timestamps/priority normalized from row
                task = PriorityTask.from_dict(row)
                if not task.created_at:
                    task.created_at = now
                task.updated_at = now
                self.tasks.append(task)
                self.save_json()
                return task
        # Local creation
        local_id = self._next_local_id()
        task = PriorityTask(task_id=local_id, title=title, due_date=due_date, status=status, priority_level=priority_n, created_at=now, updated_at=now)
        self.tasks.append(task)
        self.save_json()
        return task

    def update_task(self, task_id: int, **fields) -> Optional[PriorityTask]:
        """
        Update fields on a task (title, due_date, status, priority_level).
        Updates updated_at automatically.
        """
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if not task:
            return None
        # apply allowed fields
        for k in ("title", "due_date", "status", "priority_level"):
            if k in fields:
                if k == "priority_level":
                    setattr(task, k, _normalize_priority(fields[k]))
                else:
                    setattr(task, k, fields[k])
        task.updated_at = _now_iso()
        # persist to remote where possible
        if getattr(self.db, "supabase", None):
            # update status or priority on remote; DatabaseManager currently supports status updates only,
            # so call update_task_status for status; for priority we may re-insert or leave in sync step.
            if "status" in fields:
                try:
                    self.db.update_task_status(task_id, task.status)
                except Exception:
                    pass
        self.save_json()
        return task

    def complete_task(self, task_id: int) -> Optional[PriorityTask]:
        return self.update_task(task_id, status="Completed")

    def delete_task(self, task_id: int) -> bool:
        """
        Delete task locally and in DB (if available). Returns True if deleted.
        """
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if not task:
            return False
        if getattr(self.db, "supabase", None):
            try:
                self.db.delete_task(task_id)
            except Exception:
                pass
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        self.save_json()
        return True

    # -----------------------
    # Priority & deadline helpers
    # -----------------------
    def set_priority(self, task_id: int, priority: str) -> Optional[PriorityTask]:
        """
        Set priority for a task and persist locally (and try remote via sync).
        """
        return self.update_task(task_id, priority_level=priority)

    def get_tasks_by_priority(self, priority: str) -> List[PriorityTask]:
        p = _normalize_priority(priority)
        return [t for t in self.tasks if getattr(t, "priority_level", "Normal") == p]

    def get_overdue_tasks(self) -> List[PriorityTask]:
        today = date.today()
        overdue = []
        for t in self.tasks:
            if t.status == "Completed" or not t.due_date:
                continue
            try:
                d = datetime.fromisoformat(t.due_date).date()
                if d < today:
                    overdue.append(t)
            except Exception:
                continue
        return overdue

    def upcoming_deadlines(self, days: int = 7) -> List[PriorityTask]:
        """
        Return tasks with due_date within the next `days` days (inclusive) and not completed.
        """
        today = date.today()
        end = today + timedelta(days=days)
        upcoming = []
        for t in self.tasks:
            if t.status == "Completed" or not t.due_date:
                continue
            try:
                d = datetime.fromisoformat(t.due_date).date()
                if today <= d <= end:
                    upcoming.append(t)
            except Exception:
                continue
        return sorted(upcoming, key=lambda tt: (datetime.fromisoformat(tt.due_date).date() if tt.due_date else date.max))

    def snooze_task(self, task_id: int, days: int = 1) -> Optional[PriorityTask]:
        """
        Move a task's due_date forward by `days`. Returns updated task or None.
        """
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if not task or not task.due_date:
            return None
        try:
            d = datetime.fromisoformat(task.due_date).date()
            new_date = d + timedelta(days=days)
            task.due_date = new_date.isoformat()
            task.updated_at = _now_iso()
            self.save_json()
            return task
        except Exception:
            return None

    def compute_urgency_score(self, task: PriorityTask, now_date: Optional[date] = None) -> float:
        """
        Simple urgency score combining priority weight and proximity to due date.
        Higher score = more urgent.
        score = priority_weight * (1 + max(0, (deadline_factor)))
        deadline_factor = (max_days - days_until_due) / max_days
        """
        if now_date is None:
            now_date = date.today()
        weight = PRIORITY_WEIGHT.get(getattr(task, "priority_level", "Normal"), 2)
        if not task.due_date:
            return float(weight)
        try:
            d = datetime.fromisoformat(task.due_date).date()
        except Exception:
            return float(weight)
        days_until = (d - now_date).days
        # consider a window of 30 days for scaling
        max_days = 30.0
        deadline_factor = 0.0
        if days_until <= 0:
            deadline_factor = 1.0  # overdue or due today -> maximal urgency
        else:
            deadline_factor = max(0.0, (max_days - days_until) / max_days)
        score = weight * (1.0 + deadline_factor)
        return float(round(score, 3))

    def get_sorted_by_urgency(self) -> List[PriorityTask]:
        return sorted(self.tasks, key=lambda t: self.compute_urgency_score(t), reverse=True)

    # -----------------------
    # Sync / Helpers
    # -----------------------
    def to_list_of_dicts(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.tasks]

    def sync_with_remote(self, prefer_local: bool = True) -> Dict[str, int]:
        """
        Reconciliation between local JSON state and Supabase.

        Now preserves and syncs priority and timestamps where possible.
        """
        summary = {"pushed": 0, "pulled": 0, "updated": 0}
        if not getattr(self.db, "supabase", None):
            return summary

        try:
            remote_rows = self.db.get_all_tasks() or []
            remote_by_id = {r.get("id"): r for r in remote_rows if r.get("id") is not None}
            local_by_id = {t.task_id: t for t in self.tasks if t.task_id is not None}

            # Pull remote rows into local storage
            for rid, rrow in remote_by_id.items():
                if rid in local_by_id:
                    local = local_by_id[rid]
                    remote_simple = {
                        "title": rrow.get("title"),
                        "due_date": rrow.get("due_date"),
                        "status": rrow.get("status"),
                        "priority_level": _normalize_priority(rrow.get("priority") or rrow.get("priority_level")),
                        "created_at": rrow.get("created_at"),
                        "updated_at": rrow.get("updated_at"),
                    }
                    local_simple = {
                        "title": local.title,
                        "due_date": local.due_date,
                        "status": local.status,
                        "priority_level": getattr(local, "priority_level", "Normal"),
                        "created_at": local.created_at,
                        "updated_at": local.updated_at,
                    }
                    if not prefer_local and remote_simple != local_simple:
                        local.title = remote_simple["title"]
                        local.due_date = remote_simple["due_date"]
                        local.status = remote_simple["status"]
                        local.priority_level = remote_simple["priority_level"]
                        local.created_at = remote_simple.get("created_at", local.created_at)
                        local.updated_at = remote_simple.get("updated_at", _now_iso())
                        summary["updated"] += 1
                else:
                    # remote only -> add locally
                    self.tasks.append(PriorityTask.from_dict(rrow))
                    summary["pulled"] += 1

            # Push local-only tasks to remote
            remote_ids = set(remote_by_id.keys())
            for local in list(self.tasks):
                if local.task_id is None or local.task_id not in remote_ids:
                    # push
                    resp = self.db.add_task_to_db(local.title, local.due_date, getattr(local, "priority_level", "Normal"), local.status)
                    row = None
                    if isinstance(resp, list) and len(resp):
                        row = resp[0]
                    elif isinstance(resp, dict):
                        row = resp
                    if row and row.get("id") is not None:
                        # update local id to server id
                        local.task_id = row.get("id")
                    summary["pushed"] += 1

            # persist final local state
            self.save_json()
        except Exception as ex:
            print("❗ Sync failed:", ex)
        return summary