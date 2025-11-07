from database_manager import DatabaseManager

def main():
    db = DatabaseManager()

    # Add a new task
    db.add_task_to_db("Finish Python project", "2025-11-10", "High", "Pending")

    # Show all tasks
    print("\n📋 All Tasks:")
    tasks = db.get_all_tasks()
    for t in tasks:
        print(t)

    # Update a task’s status (replace 1 with a valid task ID)
    db.update_task_status(1, "Completed")

    # Delete a task (replace 1 with a valid task ID)
    db.delete_task(1)

if __name__ == "__main__":
    main()