import os
import sys


def get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_app_dir() -> str:
    appdata = os.getenv("APPDATA")
    if appdata:
        base_dir = appdata
    else:
        base_dir = os.path.join(os.path.expanduser("~"), ".todolist")
    app_dir = os.path.join(base_dir, "TodoList")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_logs_dir() -> str:
    logs_dir = os.path.join(get_app_dir(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def get_data_dir() -> str:
    data_dir = os.path.join(get_app_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_resource_path(relative_path: str) -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = get_project_root()
    return os.path.join(base_dir, relative_path)


def get_settings_path() -> str:
    return os.path.join(get_app_dir(), "settings.json")
