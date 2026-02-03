import os
import sys
import subprocess
import webbrowser
import time
import json
try:
    import tkinter as tk
    from tkinter import simpledialog, messagebox
except Exception:
    tk = None
    simpledialog = None
    messagebox = None
import threading
import shutil
import platform
from urllib import request as urlrequest
from urllib import error as urlerror
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
from app_paths import get_logs_dir, get_resource_path, get_project_root
from werkzeug.serving import make_server
import server as flask_server
from settings_store import load_settings, save_settings

ROOT_DIR = get_project_root()
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
SERVER_CMD = [sys.executable, "backend/cores/server.py"]
LOG_DIR = get_logs_dir()
FRONTEND_LOG = os.path.join(LOG_DIR, "frontend.log")
BACKEND_LOG = os.path.join(LOG_DIR, "backend.log")
FRONTEND_CMD = None
API_BASE = "http://127.0.0.1:5000/api"
DEV_FRONTEND_URL = "http://127.0.0.1:5173"  # Vite dev
STATIC_FRONTEND_URL = "http://127.0.0.1:5000/"
if getattr(sys, "frozen", False) and sys.platform == "darwin":
    exe_dir = os.path.dirname(sys.executable)
    ICON_PATH = os.path.abspath(os.path.join(exe_dir, "..", "Resources", "tray_mac.png"))
else:
    ICON_PATH = os.path.join(get_project_root(), "tray_mac.png")

server_proc = None
server_thread = None
frontend_proc = None
tk_root = None
last_backend_error = ""
last_frontend_error = ""
USE_TK = sys.platform != "darwin"
tray_icon = None

TRAY_LABELS = {
    "en": {
        "quick_add": "Quick add",
        "settings": "Settings",
        "open_ui": "Open UI",
        "quit": "Quit",
        "language_en": "English",
        "language_zh": "中文"
    },
    "zh": {
        "quick_add": "快速添加",
        "settings": "设置",
        "open_ui": "打开界面",
        "quit": "退出",
        "language_en": "English",
        "language_zh": "中文"
    }
}


def _apple_script_quote(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _osascript(command):
    try:
        return subprocess.run(
            ["osascript", "-e", command],
            check=False,
            capture_output=True,
            text=True
        )
    except Exception:
        return None


def _mac_dialog(message, icon=None):
    icon_part = f" with icon {icon}" if icon else ""
    script = (
        f"display dialog {_apple_script_quote(message)} "
        f"with title {_apple_script_quote('TodoList')} buttons {{\"OK\"}} "
        f"default button 1{icon_part}"
    )
    _osascript(script)


def _mac_prompt(message):
    script = (
        f'text returned of (display dialog {_apple_script_quote(message)} '
        f'with title {_apple_script_quote("TodoList")} default answer "")'
    )
    result = _osascript(script)
    if result is None or result.returncode != 0:
        return None
    return result.stdout.strip()


def create_icon_image():
    candidates = [ICON_PATH]
    if not getattr(sys, "frozen", False):
        root_fallback = os.path.join(get_project_root(), "tray_mac.png")
        if root_fallback not in candidates:
            candidates.append(root_fallback)
    for path in candidates:
        candidate_path = path
        if os.path.isdir(path):
            inner = os.path.join(path, "tray_mac.png")
            if os.path.isfile(inner):
                candidate_path = inner
            else:
                append_log(BACKEND_LOG, f"Tray icon path is a directory: {path}")
                continue
        if not os.path.isfile(candidate_path):
            continue
        try:
            image = Image.open(candidate_path).convert("RGBA")
            append_log(BACKEND_LOG, f"Tray icon loaded: {candidate_path} size={image.size}")
            return image
        except Exception as exc:
            append_log(BACKEND_LOG, f"Tray icon load failed: {candidate_path} err={exc}")
    append_log(BACKEND_LOG, f"Tray icon missing. Using fallback. Tried: {candidates}")
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([6, 6, 58, 58], radius=12, fill=(29, 78, 216, 255))
    draw.text((20, 18), "TD", fill=(255, 255, 255, 255))
    return image


def start_server():
    global server_proc, server_thread
    if getattr(sys, "frozen", False):
        if server_thread is not None:
            return
        try:
            server_thread = make_server("127.0.0.1", 5000, flask_server.app)
            threading.Thread(target=server_thread.serve_forever, daemon=True).start()
            time.sleep(0.4)
            return
        except Exception as exc:
            append_log(BACKEND_LOG, f"Failed to start embedded server: {exc}")
            server_thread = None
            raise

    if server_proc is not None and server_proc.poll() is None:
        return
    backend_log = open(BACKEND_LOG, "a", encoding="utf-8")
    server_proc = subprocess.Popen(
        SERVER_CMD,
        cwd=ROOT_DIR,
        stdout=backend_log,
        stderr=backend_log
    )
    time.sleep(0.8)


def start_frontend():
    global frontend_proc, FRONTEND_CMD
    if has_static_frontend():
        return
    if frontend_proc is not None and frontend_proc.poll() is None:
        return
    npm_cmd = shutil.which("npm")
    if not npm_cmd:
        raise RuntimeError("npm not found in PATH. Please install Node.js.")
    FRONTEND_CMD = [npm_cmd, "run", "dev"]
    frontend_log = open(FRONTEND_LOG, "a", encoding="utf-8")
    frontend_proc = subprocess.Popen(
        FRONTEND_CMD,
        cwd=FRONTEND_DIR,
        stdout=frontend_log,
        stderr=frontend_log,
        shell=False
    )
    time.sleep(1.2)


def stop_server():
    global server_proc, server_thread
    if server_thread is not None:
        try:
            server_thread.shutdown()
        except Exception:
            pass
        server_thread = None
        return
    if server_proc is None:
        return
    if server_proc.poll() is None:
        server_proc.terminate()
        server_proc.wait(timeout=3)
    server_proc = None


def stop_frontend():
    global frontend_proc
    if frontend_proc is None:
        return
    if frontend_proc.poll() is None:
        try:
            if platform.system().lower().startswith("win"):
                subprocess.run(
                    ["taskkill", "/PID", str(frontend_proc.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            else:
                frontend_proc.terminate()
                frontend_proc.wait(timeout=3)
        except Exception:
            pass
    frontend_proc = None


def open_frontend():
    webbrowser.open(get_frontend_url())


def has_static_frontend():
    packaged_dist = get_resource_path("frontend_dist")
    if os.path.isdir(packaged_dist):
        return True
    dev_dist = os.path.join(ROOT_DIR, "frontend", "dist")
    return os.path.isdir(dev_dist)


def get_frontend_url():
    if has_static_frontend():
        return STATIC_FRONTEND_URL
    return DEV_FRONTEND_URL


def is_backend_ready():
    global last_backend_error
    try:
        req = urlrequest.Request(f"{API_BASE}/list", method="GET")
        with urlrequest.urlopen(req, timeout=2):
            return True
    except Exception as exc:
        last_backend_error = str(exc)
        append_log(BACKEND_LOG, f"Backend readiness check failed: {exc}")
        return False


def is_frontend_ready():
    global last_frontend_error
    try:
        req = urlrequest.Request(get_frontend_url(), method="GET")
        with urlrequest.urlopen(req, timeout=2):
            return True
    except Exception as exc:
        last_frontend_error = str(exc)
        append_log(FRONTEND_LOG, f"Frontend readiness check failed: {exc}")
        return False


def wait_for_service(check_fn, timeout_seconds=10, interval_seconds=0.5):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if check_fn():
            return True
        time.sleep(interval_seconds)
    return False


def show_error(message):
    if sys.platform == "darwin":
        _mac_dialog(message, icon="stop")
        return
    root = init_tk_root()
    if root is None:
        return
    messagebox.showerror("TodoList", message, parent=root)


def show_info(message):
    if sys.platform == "darwin":
        _mac_dialog(message, icon="note")
        return
    root = init_tk_root()
    if root is None:
        return
    messagebox.showinfo("TodoList", message, parent=root)


def read_log_tail(path, max_lines=20):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()
        return "".join(lines[-max_lines:]).strip()
    except Exception:
        return ""


def append_log(path, message):
    try:
        with open(path, "a", encoding="utf-8", errors="ignore") as file:
            file.write(message)
            if not message.endswith("\n"):
                file.write("\n")
    except Exception:
        pass


def api_add_task(description, details="", due_date=None):
    payload = {
        "description": description,
        "details": details,
        "due_date": due_date
    }
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        f"{API_BASE}/add",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlrequest.urlopen(req, timeout=5):
        pass


def init_tk_root():
    global tk_root
    if not USE_TK or tk is None:
        return None
    if tk_root is not None:
        return tk_root
    tk_root = tk.Tk()
    tk_root.withdraw()
    tk_root.attributes("-topmost", True)
    return tk_root


def prompt_quick_add(root):
    if sys.platform == "darwin":
        description = _mac_prompt("Task description:")
        if not description:
            return None
        details = _mac_prompt("Details (optional):")
        due_date = _mac_prompt("Due date (YYYY-MM-DD, optional):")
        return description.strip(), (details or "").strip(), (due_date or "").strip() or None
    description = simpledialog.askstring("Quick Add", "Task description:", parent=root)
    if not description:
        return None

    details = simpledialog.askstring("Quick Add", "Details (optional):", parent=root)
    due_date = simpledialog.askstring("Quick Add", "Due date (YYYY-MM-DD, optional):", parent=root)

    return description.strip(), (details or "").strip(), (due_date or "").strip() or None


def quick_add_flow():
    try:
        root = init_tk_root()
        result = prompt_quick_add(root)
        if not result:
            return
        description, details, due_date = result
        if not description:
            return
        api_add_task(description, details, due_date)
    except urlerror.URLError as exc:
        show_error(f"Failed to add task:\n{exc}")
    except Exception as exc:
        show_error(f"Unexpected error:\n{exc}")


def quick_add_task(icon, _item):
    start_server()
    if USE_TK and tk_root is None:
        init_tk_root()
    if USE_TK and tk_root is not None:
        tk_root.after(0, quick_add_flow)
    else:
        threading.Thread(target=quick_add_flow, daemon=True).start()


def set_language(lang):
    save_settings({"language": lang})
    refresh_menu()


def get_language():
    lang = load_settings().get("language", "en")
    if lang not in TRAY_LABELS:
        return "en"
    return lang


def build_menu():
    labels = TRAY_LABELS[get_language()]
    language_menu = pystray.Menu(
        item(labels["language_en"], lambda _icon, _item: set_language("en")),
        item(labels["language_zh"], lambda _icon, _item: set_language("zh"))
    )
    return pystray.Menu(
        item(labels["quick_add"], quick_add_task),
        item(labels["settings"], language_menu),
        item(labels["open_ui"], lambda _icon, _item: open_frontend()),
        item(labels["quit"], quit_app)
    )


def refresh_menu():
    global tray_icon
    if tray_icon is None:
        return
    tray_icon.menu = build_menu()
    try:
        tray_icon.update_menu()
    except Exception:
        pass


def quit_app(icon, _item):
    stop_server()
    stop_frontend()
    icon.stop()
    if tk_root is not None:
        tk_root.after(0, tk_root.quit)


def start_services(show_success):
    try:
        start_server()
    except Exception as exc:
        backend_tail = read_log_tail(BACKEND_LOG)
        show_error(
            "Backend failed to start. Check Flask server.\n\n"
            f"Error: {exc}\n\n"
            f"Backend log tail:\n{backend_tail}"
        )
        return
    try:
        start_frontend()
    except Exception as exc:
        show_error(f"Failed to start frontend:\n{exc}")
        return

    backend_ok = wait_for_service(is_backend_ready, timeout_seconds=8, interval_seconds=0.5)
    frontend_ok = wait_for_service(is_frontend_ready, timeout_seconds=12, interval_seconds=0.5)

    if backend_ok and frontend_ok:
        if show_success:
            show_info("Backend and frontend started successfully.")
        return

    if not backend_ok and not frontend_ok:
        backend_tail = read_log_tail(BACKEND_LOG)
        frontend_tail = read_log_tail(FRONTEND_LOG)
        show_error(
            "Failed to start backend and frontend.\n\n"
            f"Backend log tail:\n{backend_tail}\n\n"
            f"Frontend log tail:\n{frontend_tail}"
        )
        return

    if not backend_ok:
        backend_tail = read_log_tail(BACKEND_LOG)
        show_error(
            "Backend failed to start. Check Flask server.\n\n"
            f"Last error: {last_backend_error}\n\n"
            f"Backend log tail:\n{backend_tail}"
        )
        return

    frontend_tail = read_log_tail(FRONTEND_LOG)
    show_error(
        "Frontend is not running. Make sure Vite is started.\n\n"
        f"Frontend log tail:\n{frontend_tail}"
    )


def main():
    global tray_icon
    tray_icon = pystray.Icon("todolist", create_icon_image(), "TodoList", build_menu())
    if USE_TK:
        threading.Thread(target=tray_icon.run, daemon=True).start()
        init_tk_root()
        if tk_root is None:
            start_services(show_success=False)
            return
        tk_root.after(0, lambda: start_services(show_success=False))
        tk_root.mainloop()
    else:
        threading.Thread(target=lambda: start_services(show_success=False), daemon=True).start()
        tray_icon.run()


if __name__ == "__main__":
    main()
