import os
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List, Dict, Optional

JSON_FALLBACK_FILE = "tasks.json"


class DatabaseManager:
    def __init__(self, use_json_fallback_if_no_env: bool = True):
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.supabase: Optional[Client] = None
        if self.url and self.key:
            try:
                self.supabase = create_client(self.url, self.key)
                print("✅ Connected to Supabase successfully!")
            except Exception as ex:
                print("⚠️ Supabase client init failed:", ex)
                if not use_json_fallback_if_no_env:
                    raise
        else:
            print("⚠️ SUPABASE_URL or SUPABASE_KEY not found in environment.")
            if not use_json_fallback_if_no_env:
                raise EnvironmentError("Supabase credentials are required")

        if not os.path.exists(JSON_FALLBACK_FILE):
            with open(JSON_FALLBACK_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    # Core CRUD
    def add_task_to_db(self, title: str, due_date: str, priority: str, status: str = "Pending") -> Optional[Dict]:
        data = {"title": title, "due_date": due_date, "priority": priority, "status": status}
        if self.supabase:
            try:
                response = self.supabase.table("tasks").insert(data).execute()
                print("🟢 Task added:", response.data)
                return response.data
            except Exception as ex:
                print("❗ Supabase insert failed:", ex)
                return None
        # JSON fallback
        tasks = self._load_json_tasks()
        next_id = max((t.get("id", 0) for t in tasks), default=0) + 1
        data_with_id = {"id": next_id, **data}
        tasks.append(data_with_id)
        self._save_json_tasks(tasks)
        print("🟢 Task added to JSON fallback:", data_with_id)
        return data_with_id

    def get_all_tasks(self) -> List[Dict]:
        if self.supabase:
            try:
                response = self.supabase.table("tasks").select("*").order("id").execute()
                return response.data or []
            except Exception as ex:
                print("❗ Supabase select failed:", ex)
                return []
        return self._load_json_tasks()

    def update_task_status(self, task_id: int, new_status: str) -> Optional[Dict]:
        if self.supabase:
            try:
                response = (
                    self.supabase.table("tasks")
                    .update({"status": new_status})
                    .eq("id", task_id)
                    .execute()
                )
                print("🟡 Task updated:", response.data)
                return response.data
            except Exception as ex:
                print("❗ Supabase update failed:", ex)
                return None
        tasks = self._load_json_tasks()
        for t in tasks:
            if t.get("id") == task_id:
                t["status"] = new_status
                self._save_json_tasks(tasks)
                print("🟡 Task updated in JSON fallback:", t)
                return t
        print("⚠️ Task not found in JSON fallback:", task_id)
        return None

    def delete_task(self, task_id: int) -> Optional[Dict]:
        if self.supabase:
            try:
                response = self.supabase.table("tasks").delete().eq("id", task_id).execute()
                print("🔴 Task deleted:", response.data)
                return response.data
            except Exception as ex:
                print("❗ Supabase delete failed:", ex)
                return None
        tasks = self._load_json_tasks()
        new_tasks = [t for t in tasks if t.get("id") != task_id]
        if len(new_tasks) == len(tasks):
            print("⚠️ Task not found in JSON fallback:", task_id)
            return None
        self._save_json_tasks(new_tasks)
        print("🔴 Task deleted from JSON fallback:", task_id)
        return {"deleted_id": task_id}

    # Analytics helpers (useful for GUI)
    def get_completed_counts_per_day(self, days_back: int = 14) -> Dict[str, int]:
        """
        Returns dict mapping YYYY-MM-DD -> completed_count for the last `days_back` days.
        """
        end = datetime.utcnow().date()
        start = end - timedelta(days=days_back - 1)
        counts = defaultdict(int)

        if self.supabase:
            try:
                response = (
                    self.supabase.table("tasks")
                    .select("id,due_date,created_at,updated_at,completed_at")
                    .eq("status", "Completed")
                    .gte("due_date", str(start))  
                    .lte("due_date", str(end))
                    .execute()
                )
                rows = response.data or []
                for r in rows:
                    d = r.get("completed_at") or r.get("updated_at") or r.get("due_date") or r.get("created_at")
                    if not d:
                        continue
                    day = d.split("T")[0] if "T" in d else str(d)
                    counts[day] += 1
            except Exception as ex:
                print("❗ Supabase analytics query failed:", ex)
        else:
            for t in self._load_json_tasks():
                if t.get("status") == "Completed":
                    d = t.get("completed_at") or t.get("updated_at") or t.get("due_date")
                    if not d:
                        continue
                    if start <= datetime.fromisoformat(d).date() <= end:
                        counts[d.split("T")[0] if "T" in d else d] += 1

        result = {}
        for i in range(days_back):
            day = str(start + timedelta(days=i))
            result[day] = counts.get(day, 0)
        return result

    def get_priority_distribution(self) -> Dict[str, int]:
        """
        Returns counts per priority for all tasks.
        """
        counter = Counter()
        if self.supabase:
            try:
                response = self.supabase.table("tasks").select("priority,status").execute()
                rows = response.data or []
                for r in rows:
                    p = r.get("priority") or "Unknown"
                    counter[p] += 1
            except Exception as ex:
                print("❗ Supabase priority query failed:", ex)
        else:
            for t in self._load_json_tasks():
                counter[t.get("priority", "Unknown")] += 1
        return dict(counter)

    # JSON fallback helpers
    def _load_json_tasks(self) -> List[Dict]:
        try:
            with open(JSON_FALLBACK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_json_tasks(self, tasks: List[Dict]):
        try:
            with open(JSON_FALLBACK_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)
        except Exception as ex:
            print("❗ Failed to save JSON fallback:", ex)

    # Utility: helpful but non-destructive
    def create_table_in_supabase(self):
        raise NotImplementedError("Use Supabase SQL Editor or provide permission to run DDL.")