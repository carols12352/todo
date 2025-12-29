import os
import sqlite3
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

os.makedirs("logs", exist_ok=True)
file_handler = RotatingFileHandler(
    "logs/app.log", maxBytes=1024*1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

def SQLinit(name: str):
    try:
        base_dir = os.path.dirname(__file__)
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        db_path = os.path.join(data_dir, f"{name}.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            details TEXT,
            completed BOOLEAN DEFAULT 0,
            due_date DATE
        )
        """)

        conn.commit()
        conn.close()

        logger.debug(f"Database '{name}.db' initialized successfully at {db_path}")
        return db_path

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_db_path(name: str) -> str:
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")
    db_path = os.path.join(data_dir, f"{name}.db")
    return db_path