import json
from app_paths import get_settings_path


DEFAULT_SETTINGS = {
    "language": "en"
}


def load_settings() -> dict:
    path = get_settings_path()
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            return DEFAULT_SETTINGS.copy()
        return {**DEFAULT_SETTINGS, **data}
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    path = get_settings_path()
    data = {**DEFAULT_SETTINGS, **(settings or {})}
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
