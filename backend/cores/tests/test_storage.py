import pytest
import sqlite3
import os
from ..storage import SQLStorage
from ..dbinit import SQLinit

@pytest.fixture
def setup_database():
    db_path = SQLinit("test_tasks")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    yield cursor
    conn.close()
    os.remove(db_path)






