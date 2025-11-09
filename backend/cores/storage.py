import sqlite3
import logging
import os
from logging.handlers import RotatingFileHandler
from dbinit import get_db_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

os.makedirs("logs", exist_ok=True)
file_handler = RotatingFileHandler(
    "logs/app.log", maxBytes=1024 * 1024, backupCount=5, encoding="utf-8"
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
                INSERT INTO tasks (description, details, completed, due_date)
                VALUES (?, ?, ?, ?)
            """, (
                task["description"],
                task["details"],
                task["completed"],
                task["due_date"]
            ))
            conn.commit()
            logger.debug(f"Task added: {task}")

    def list_tasks(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
            logger.debug(f"Listed {len(rows)} tasks.")

    def done_task(self, task_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                print(f"Task ID {task_id} not found.")
                logger.warning(f"Task ID {task_id} not found to mark as done.")
                return
            conn.commit()
            logger.debug(f"Task marked as done: ID={task_id}")
            print(f"Task ID {task_id} marked as done.")

    def remove_task(self, task_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                print(f"Task ID {task_id} not found.")
                logger.warning(f"Task ID {task_id} not found for removal.")
                return
            conn.commit()
            logger.debug(f"Task removed: ID={task_id}")
            print(f"Task ID {task_id} removed.")
