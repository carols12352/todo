import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from app_paths import get_data_dir, get_logs_dir

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(
    f"{get_logs_dir()}/app.log", maxBytes=1024*1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

def SQLinit(name: str):
    try:
        data_dir = get_data_dir()
        db_path = f"{data_dir}/{name}.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            details TEXT,
            completed BOOLEAN DEFAULT 0,
            due_date DATE,
            category TEXT DEFAULT 'personal',
            priority TEXT DEFAULT 'medium',
            color TEXT
        )
        """)

        cursor.execute("PRAGMA table_info(tasks)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if "category" not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'personal'")
        if "priority" not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
        if "color" not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN color TEXT")

        cursor.execute("UPDATE tasks SET category = 'personal' WHERE category IS NULL")
        cursor.execute("UPDATE tasks SET priority = 'medium' WHERE priority IS NULL")

        conn.commit()
        conn.close()

        logger.debug(f"Database '{name}.db' initialized successfully at {db_path}")
        return db_path

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_db_path(name: str) -> str:
    data_dir = get_data_dir()
    return f"{data_dir}/{name}.db"
