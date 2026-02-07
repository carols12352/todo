import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from dbinit import get_db_path
from app_paths import get_logs_dir

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(
    f"{get_logs_dir()}/app.log", maxBytes=1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)


class SQLStorage:
    def __init__(self, db_name="tasks"):
        self.db_path = get_db_path(db_name)
        logger.debug(f"Database path resolved: {self.db_path}")

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)

    def add_task(self, task):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (description, details, completed, due_date, category, priority, color, all_day, datetime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task["description"],
                task.get("details", ""),
                task.get("completed", False),
                task.get("due_date"),
                task.get("category", "personal"),
                task.get("priority", "medium"),
                task.get("color"),
                task.get("all_day"),
                task.get("datetime"),
            ))
            conn.commit()
            task_id = cursor.lastrowid
            logger.debug(f"Task added: ID={task_id}")
            return task_id

    def list_tasks(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
            logger.debug(f"Listed {len(rows)} tasks.")
    
    def list_task_flasks(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            rows = cursor.fetchall()
            tasks = []
            for row in rows:
                task = {
                    "id": row[0],
                    "description": row[1],
                    "details": row[2],
                    "completed": bool(row[3]),
                    "due_date": row[4],
                    "category": row[5],
                    "priority": row[6],
                    "color": row[7],
                    "all_day": bool(row[8]) if row[8] is not None else None,
                    "datetime": row[9],
                }
                tasks.append(task)
            logger.debug(f"Listed {len(tasks)} tasks.")
            return tasks

    def done_task(self, task_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                print(f"Task ID {task_id} not found.")
                logger.warning(f"Task ID {task_id} not found to mark as done.")
                return False
            conn.commit()
            logger.debug(f"Task marked as done: ID={task_id}")
            print(f"Task ID {task_id} marked as done.")
            return True

    def remove_task(self, task_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                print(f"Task ID {task_id} not found.")
                logger.warning(f"Task ID {task_id} not found for removal.")
                return False
            conn.commit()
            logger.debug(f"Task removed: ID={task_id}")
            print(f"Task ID {task_id} removed.")
            return True

    def reopen_task(self, task_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET completed = 0 WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                print(f"Task ID {task_id} not found.")
                logger.warning(f"Task ID {task_id} not found to reopen.")
                return False
            conn.commit()
            logger.debug(f"Task reopened: ID={task_id}")
            print(f"Task ID {task_id} reopened.")
            return True

    def update_task(self, task_id, description, details, due_date, category, priority, color, all_day, datetime_value):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks
                SET description = ?, details = ?, due_date = ?, category = ?, priority = ?, color = ?, all_day = ?, datetime = ?
                WHERE id = ?
                """,
                (description, details, due_date, category, priority, color, all_day, datetime_value, task_id)
            )
            if cursor.rowcount == 0:
                logger.warning(f"Task ID {task_id} not found to update.")
                return False
            conn.commit()
            logger.debug(f"Task updated: ID={task_id}")
            return True
