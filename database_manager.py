from supabase import create_client, Client

class DatabaseManager:
    def __init__(self):
        # ⚠️ Replace these with your Supabase credentials
        self.url = "https://hymhusvcsztuwckubxvg.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh5bWh1c3Zjc3p0dXdja3VieHZnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1MjkzNTksImV4cCI6MjA3ODEwNTM1OX0.DsrbOwnWi7pYJjYNm7tF1axlobjGXkzibKDGKHBWmM8"

        self.supabase: Client = create_client(self.url, self.key)
        print("✅ Connected to Supabase successfully!")

    # ➕ Create (Add Task)
    def add_task_to_db(self, title, due_date, priority, status):
        data = {
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "status": status
        }
        response = self.supabase.table("tasks").insert(data).execute()
        print("🟢 Task added:", response.data)

    # 📋 Read (Get All Tasks)
    def get_all_tasks(self):
        response = self.supabase.table("tasks").select("*").execute()
        return response.data

    # 🔄 Update (Change Status)
    def update_task_status(self, task_id, new_status):
        response = (
            self.supabase
            .table("tasks")
            .update({"status": new_status})
            .eq("id", task_id)
            .execute()
        )
        print("🟡 Task updated:", response.data)

    # ❌ Delete
    def delete_task(self, task_id):
        response = self.supabase.table("tasks").delete().eq("id", task_id).execute()
        print("🔴 Task deleted:", response.data)