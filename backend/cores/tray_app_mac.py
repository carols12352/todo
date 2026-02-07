import os
import sys
import subprocess
import webbrowser
import time
import json
from datetime import date, timedelta
try:
    import tkinter as tk
    from tkinter import simpledialog, messagebox, ttk
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
import traceback
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
USE_TK = tk is not None
tray_icon = None
last_language = None
ai_warmed = False

TRAY_LABELS = {
    "en": {
        "quick_add": "AI Quick Add",
        "settings": "Settings",
        "language": "Language",
        "open_ui": "Open UI",
        "quit": "Quit",
        "language_en": "English",
        "language_zh": "中文"
    },
    "zh": {
        "quick_add": "AI 快速添加",
        "settings": "设置",
        "language": "语言",
        "open_ui": "打开界面",
        "quit": "退出",
        "language_en": "English",
        "language_zh": "中文"
    }
}

AI_DIALOG_LABELS = {
    "en": {
        "title": "AI Quick Add",
        "section_command": "Command",
        "section_parsed": "Parsed Result",
        "section_task": "Task Details",
        "command": "AI Command:",
        "analyze": "Analyze",
        "action": "Action",
        "target": "Target",
        "title_label": "Title",
        "details": "Details",
        "due_date": "Due date",
        "due_time": "Time (HH:MM)",
        "all_day": "All day",
        "category": "Category",
        "priority": "Priority",
        "confirm": "Confirm",
        "cancel": "Cancel",
        "status": "Analyzing...",
        "warn_command": "Please enter a command.",
        "warn_target": "Missing target task ID.",
    },
    "zh": {
        "title": "AI 快速添加",
        "section_command": "指令",
        "section_parsed": "解析结果",
        "section_task": "任务详情",
        "command": "AI 指令：",
        "analyze": "解析",
        "action": "动作",
        "target": "目标",
        "title_label": "标题",
        "details": "详情",
        "due_date": "日期",
        "due_time": "时间 (HH:MM)",
        "all_day": "全天",
        "category": "分类",
        "priority": "优先级",
        "confirm": "确认",
        "cancel": "取消",
        "status": "解析中...",
        "warn_command": "请输入指令。",
        "warn_target": "缺少目标任务 ID。",
    },
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


def _mac_choose_from_list(message, options):
    options_list = ", ".join(_apple_script_quote(opt) for opt in options)
    script = (
        f"set choices to {{{options_list}}}\n"
        f"set chosen to choose from list choices with prompt {_apple_script_quote(message)}\n"
        f"if chosen is false then return \"\" else return item 1 of chosen as string"
    )
    result = _osascript(script)
    if result is None or result.returncode != 0:
        return ""
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


def apply_macos_template(icon):
    try:
        import AppKit  # type: ignore
        status_item = getattr(icon, "_status_item", None)
        if not status_item:
            return
        button = status_item.button()
        if not button:
            return
        image = button.image()
        if image:
            image.setTemplate_(True)
    except Exception:
        pass


def ensure_macos_template(icon, retries=10, delay=0.2):
    if sys.platform != "darwin":
        return
    for _ in range(retries):
        try:
            apply_macos_template(icon)
            status_item = getattr(icon, "_status_item", None)
            if status_item and status_item.button() and status_item.button().image():
                return
        except Exception:
            pass
        time.sleep(delay)


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


def _trim_log_if_needed(path, max_bytes=2 * 1024 * 1024, keep_lines=2000):
    try:
        if not os.path.exists(path):
            return
        if os.path.getsize(path) <= max_bytes:
            return
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()
        tail = lines[-keep_lines:] if len(lines) > keep_lines else lines
        with open(path, "w", encoding="utf-8", errors="ignore") as file:
            file.writelines(tail)
    except Exception:
        pass


def append_log(path, message):
    try:
        _trim_log_if_needed(path)
        with open(path, "a", encoding="utf-8", errors="ignore") as file:
            file.write(message)
            if not message.endswith("\n"):
                file.write("\n")
    except Exception:
        pass


def api_add_task(description, details="", due_date=None, all_day=None, datetime_value=None):
    payload = {
        "description": description,
        "details": details,
        "due_date": due_date,
        "all_day": all_day if all_day is not None else (True if due_date else None),
        "datetime": datetime_value if datetime_value is not None else (due_date if due_date else None),
    }
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        f"{API_BASE}/add",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlrequest.urlopen(req, timeout=5) as response:
        payload = response.read().decode("utf-8") or "{}"
    try:
        return json.loads(payload).get("task_id")
    except Exception:
        return None


def api_update_task(task_id, payload):
    data = json.dumps({"id": task_id, **payload}).encode("utf-8")
    req = urlrequest.Request(
        f"{API_BASE}/update",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlrequest.urlopen(req, timeout=5):
        pass


def api_remove_task(task_id):
    payload = {"id": task_id}
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        f"{API_BASE}/remove",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlrequest.urlopen(req, timeout=5):
        pass


def api_reopen_task(task_id):
    payload = {"id": task_id}
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        f"{API_BASE}/reopen",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlrequest.urlopen(req, timeout=5):
        pass


def api_ai_parse(text, timeout_seconds=45):
    payload = {"text": text}
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        f"{API_BASE}/ai/parse",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlrequest.urlopen(req, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8") or "{}"
    return json.loads(body)


def api_ai_warm():
    global ai_warmed
    if ai_warmed:
        return
    try:
        req = urlrequest.Request(f"{API_BASE}/ai/warm", method="POST")
        with urlrequest.urlopen(req, timeout=10):
            pass
        ai_warmed = True
    except Exception as exc:
        append_log(BACKEND_LOG, f"AI warm failed: {exc}")


def api_ai_unload():
    req = urlrequest.Request(f"{API_BASE}/ai/unload", method="POST")
    with urlrequest.urlopen(req, timeout=10):
        pass


def api_mark_done(task_id):
    payload = {"id": task_id}
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        f"{API_BASE}/done",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlrequest.urlopen(req, timeout=5):
        pass


def api_set_language(lang):
    payload = {"language": lang}
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        f"{API_BASE}/settings",
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
    if platform.system().lower().startswith("win"):
        try:
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    tk_root = tk.Tk()
    try:
        scale = tk_root.winfo_fpixels("1i") / 72.0
        tk_root.tk.call("tk", "scaling", scale)
    except Exception:
        pass
    tk_root.withdraw()
    tk_root.attributes("-topmost", True)
    append_log(BACKEND_LOG, "Tk root initialized.")
    return tk_root


def _build_datetime_payload(due_date, due_time, all_day):
    if not due_date:
        return None, None
    if all_day or not due_time:
        return True, due_date
    return False, f"{due_date}T{due_time}"


def _normalize_ai_result(result):
    action = result.get("action") or "add"
    target_id = (result.get("target") or {}).get("id")
    patch = result.get("task_patch") or {}
    return action, target_id, patch


def prompt_ai_quick_add(root):
    if root is None:
        return None

    lang = get_language()
    labels = AI_DIALOG_LABELS.get(lang, AI_DIALOG_LABELS["en"])

    try:
        dialog = tk.Toplevel(root)
        dialog.title(labels["title"])
        dialog.geometry("700x760")
        dialog.minsize(680, 720)
        dialog.resizable(True, True)
        dialog.attributes("-topmost", True)
        try:
            screen_w = dialog.winfo_screenwidth()
            screen_h = dialog.winfo_screenheight()
            x = max((screen_w - 700) // 2, 0)
            y = max((screen_h - 760) // 2, 0)
            dialog.geometry(f"700x760+{x}+{y}")
        except Exception:
            pass
        dialog.update_idletasks()
        dialog.deiconify()
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
    except Exception as exc:
        append_log(BACKEND_LOG, f"AI dialog init failed: {exc}\n{traceback.format_exc()}")
        raise
    dialog.lift()
    dialog.focus_force()

    state = {"parsed": False, "action": "add", "target_id": None}
    command_var = tk.StringVar(dialog, value="")
    action_var = tk.StringVar(dialog, value=f"{labels['action']}: -")
    target_var = tk.StringVar(dialog, value=f"{labels['target']}: -")
    status_var = tk.StringVar(dialog, value="")
    description_var = tk.StringVar(dialog, value="")
    due_date_var = tk.StringVar(dialog, value="")
    due_time_var = tk.StringVar(dialog, value="")
    all_day_var = tk.BooleanVar(dialog, value=True)
    category_var = tk.StringVar(dialog, value="personal")
    priority_var = tk.StringVar(dialog, value="medium")
    result = {"value": None}
    details_text = None

    def parse_command():
        text = command_var.get().strip()
        if not text:
            messagebox.showwarning("TodoList", labels["warn_command"], parent=dialog)
            return
        try:
            status_var.set(labels["status"])
            progress.start(8)
            dialog.configure(cursor="watch")
            analyze_btn.state(["disabled"])
            confirm_btn.state(["disabled"])
            dialog.update_idletasks()
            ai_result = api_ai_parse(text)
        except Exception as exc:
            status_var.set("")
            progress.stop()
            dialog.configure(cursor="")
            analyze_btn.state(["!disabled"])
            confirm_btn.state(["!disabled"])
            messagebox.showerror("TodoList", f"AI parse failed:\n{exc}", parent=dialog)
            return
        status_var.set("")
        progress.stop()
        dialog.configure(cursor="")
        analyze_btn.state(["!disabled"])
        confirm_btn.state(["!disabled"])
        action, target_id, patch = _normalize_ai_result(ai_result)
        state["parsed"] = True
        state["action"] = action
        state["target_id"] = target_id
        action_var.set(f"{labels['action']}: {action}")
        target_var.set(f"{labels['target']}: {target_id if target_id is not None else '-'}")

        description_var.set(patch.get("description") or "")
        if details_text is not None:
            details_text.delete("1.0", "end")
            details_text.insert("1.0", patch.get("details") or "")
        due_date_var.set(patch.get("due_date") or "")
        due_time_var.set(patch.get("due_time") or "")
        if patch.get("all_day") is None:
            all_day_var.set(True if patch.get("due_date") and not patch.get("due_time") else False)
        else:
            all_day_var.set(bool(patch.get("all_day")))
        category_var.set(patch.get("category") or "personal")
        priority_var.set(patch.get("priority") or "medium")

    def on_confirm():
        if not state["parsed"]:
            parse_command()
            if not state["parsed"]:
                return
        action = state["action"]
        target_id = state["target_id"]
        if action in ("done", "reopen", "remove") and target_id is None:
            messagebox.showwarning("TodoList", labels["warn_target"], parent=dialog)
            return
        if action in ("add", "update"):
            all_day, datetime_value = _build_datetime_payload(
                due_date_var.get().strip(),
                due_time_var.get().strip(),
                all_day_var.get()
            )
            payload = {
                "description": description_var.get().strip(),
                "details": (details_text.get("1.0", "end") if details_text else "").strip(),
                "due_date": due_date_var.get().strip() or None,
                "all_day": all_day,
                "datetime": datetime_value,
                "category": category_var.get().strip() or "personal",
                "priority": priority_var.get().strip() or "medium",
                "color": None,
            }
        else:
            payload = None

        result["value"] = (action, target_id, payload)
        dialog.destroy()

    def on_cancel():
        result["value"] = None
        dialog.destroy()

    style = ttk.Style(dialog)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("AI.TLabel", font=("Segoe UI", 10))
    style.configure("AI.Title.TLabel", font=("Segoe UI", 10, "bold"))
    style.configure("AI.TButton", font=("Segoe UI", 10), padding=(10, 4))
    style.configure("AI.TEntry", font=("Segoe UI", 10))
    style.configure("AI.TCheckbutton", font=("Segoe UI", 10))

    container = ttk.Frame(dialog, padding=18)
    container.pack(fill="both", expand=True)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(2, weight=1)

    command_frame = ttk.LabelFrame(container, text=labels["section_command"], padding=12)
    command_frame.grid(row=0, column=0, sticky="ew")
    command_frame.columnconfigure(0, weight=1)
    ttk.Label(command_frame, text=labels["command"], style="AI.Title.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Entry(command_frame, textvariable=command_var, style="AI.TEntry").grid(row=1, column=0, sticky="ew", pady=(6, 10))
    toolbar = ttk.Frame(command_frame)
    toolbar.grid(row=2, column=0, sticky="w")
    analyze_btn = ttk.Button(toolbar, text=labels["analyze"], command=parse_command, style="AI.TButton")
    analyze_btn.pack(side="left")
    ttk.Label(toolbar, textvariable=status_var, foreground="#2563eb", style="AI.TLabel").pack(side="left", padx=(10, 0))
    progress = ttk.Progressbar(command_frame, mode="indeterminate")
    progress.grid(row=3, column=0, sticky="ew", pady=(6, 0))

    meta = ttk.LabelFrame(container, text=labels["section_parsed"], padding=10)
    meta.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    meta.columnconfigure(0, weight=1)
    ttk.Label(meta, textvariable=action_var, style="AI.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(meta, textvariable=target_var, style="AI.TLabel").grid(row=1, column=0, sticky="w")

    form = ttk.LabelFrame(container, text=labels["section_task"], padding=12)
    form.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
    form.columnconfigure(1, weight=1)
    form.rowconfigure(1, weight=1)

    ttk.Label(form, text=labels["title_label"], style="AI.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
    ttk.Entry(form, textvariable=description_var, style="AI.TEntry").grid(row=0, column=1, sticky="ew", pady=(0, 8))

    ttk.Label(form, text=labels["details"], style="AI.TLabel").grid(row=1, column=0, sticky="nw", pady=(0, 8))
    details_text = tk.Text(form, height=6, wrap="word", font=("Segoe UI", 10))
    details_text.grid(row=1, column=1, sticky="nsew", pady=(0, 8))

    ttk.Label(form, text=labels["due_date"], style="AI.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 8))
    ttk.Entry(form, textvariable=due_date_var, width=18, style="AI.TEntry").grid(row=2, column=1, sticky="w", pady=(0, 8))

    ttk.Label(form, text=labels["due_time"], style="AI.TLabel").grid(row=3, column=0, sticky="w", pady=(0, 8))
    ttk.Entry(form, textvariable=due_time_var, width=18, style="AI.TEntry").grid(row=3, column=1, sticky="w", pady=(0, 8))

    ttk.Checkbutton(form, text=labels["all_day"], variable=all_day_var, style="AI.TCheckbutton").grid(row=4, column=1, sticky="w", pady=(0, 10))

    ttk.Label(form, text=labels["category"], style="AI.TLabel").grid(row=5, column=0, sticky="w", pady=(0, 8))
    ttk.OptionMenu(form, category_var, "personal", "work", "study", "personal").grid(row=5, column=1, sticky="w", pady=(0, 8))

    ttk.Label(form, text=labels["priority"], style="AI.TLabel").grid(row=6, column=0, sticky="w", pady=(0, 8))
    ttk.OptionMenu(form, priority_var, "medium", "high", "medium", "low").grid(row=6, column=1, sticky="w", pady=(0, 8))

    actions = ttk.Frame(container)
    actions.grid(row=3, column=0, sticky="se", pady=(12, 0))
    ttk.Button(actions, text=labels["cancel"], command=on_cancel, style="AI.TButton").pack(side="right")
    confirm_btn = ttk.Button(actions, text=labels["confirm"], command=on_confirm, style="AI.TButton")
    confirm_btn.pack(side="right", padx=(8, 0))

    dialog.wait_window()
    return result["value"]


def quick_add_flow():
    try:
        append_log(BACKEND_LOG, "Quick add flow started.")
        root = init_tk_root()
        append_log(BACKEND_LOG, "Opening AI quick add dialog.")
        result = prompt_ai_quick_add(root)
        append_log(BACKEND_LOG, f"AI quick add dialog closed. Result: {'ok' if result else 'cancel'}")
        if not result:
            return
        action, target_id, payload = result
        if action == "done" and target_id is not None:
            api_mark_done(target_id)
            return
        if action == "reopen" and target_id is not None:
            api_reopen_task(target_id)
            return
        if action == "remove" and target_id is not None:
            api_remove_task(target_id)
            return
        if action == "update" and target_id is not None and payload is not None:
            api_update_task(target_id, payload)
            return
        if payload is not None:
            api_add_task(
                payload.get("description", ""),
                payload.get("details", ""),
                payload.get("due_date"),
                payload.get("all_day"),
                payload.get("datetime"),
            )
    except urlerror.URLError as exc:
        append_log(BACKEND_LOG, f"Quick add URL error: {exc}")
        show_error(f"Failed to add task:\n{exc}")
    except Exception as exc:
        append_log(BACKEND_LOG, f"Quick add error: {exc}\n{traceback.format_exc()}")
        show_error(f"Unexpected error:\n{exc}")
    finally:
        pass


def quick_add_task(icon, _item):
    append_log(BACKEND_LOG, "Tray menu clicked: quick_add")
    start_server()
    if USE_TK and tk_root is not None:
        tk_root.after(0, quick_add_flow)
        return
    if USE_TK:
        append_log(BACKEND_LOG, "Quick add requested before Tk root is ready.")
        return
    threading.Thread(target=quick_add_flow, daemon=True).start()


def set_language(lang):
    save_settings({"language": lang})
    try:
        api_set_language(lang)
    except Exception:
        pass
    refresh_menu()


def get_language():
    lang = load_settings().get("language", "en")
    if lang not in TRAY_LABELS:
        return "en"
    return lang


def build_menu():
    labels = TRAY_LABELS[get_language()]
    current_lang = get_language()
    language_menu = pystray.Menu(
        item(
            labels["language_en"],
            lambda _icon, _item: set_language("en"),
            checked=lambda _item: current_lang == "en"
        ),
        item(
            labels["language_zh"],
            lambda _icon, _item: set_language("zh"),
            checked=lambda _item: current_lang == "zh"
        )
    )
    settings_menu = pystray.Menu(
        item(labels["language"], language_menu)
    )
    return pystray.Menu(
        item(labels["quick_add"], quick_add_task),
        item(labels["settings"], settings_menu),
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


def watch_language_changes(interval_seconds=2.0):
    global last_language
    while True:
        try:
            current = get_language()
            if last_language is None:
                last_language = current
            elif current != last_language:
                last_language = current
                refresh_menu()
        except Exception:
            pass
        time.sleep(interval_seconds)


def quit_app(icon, _item):
    try:
        api_ai_unload()
    except Exception:
        pass
    stop_server()
    stop_frontend()
    icon.stop()
    if tk_root is not None:
        tk_root.after(0, tk_root.quit)
        tk_root.after(0, tk_root.destroy)
    os._exit(0)


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
        threading.Thread(target=api_ai_warm, daemon=True).start()
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
    if sys.platform == "darwin":
        threading.Thread(target=lambda: ensure_macos_template(tray_icon), daemon=True).start()
    threading.Thread(target=watch_language_changes, daemon=True).start()
    if USE_TK:
        init_tk_root()
        threading.Thread(target=tray_icon.run, daemon=True).start()
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
