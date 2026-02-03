import os
import flask
import logging
import traceback
from flask_cors import CORS
from storage import SQLStorage
from dbinit import SQLinit
from settings_store import load_settings, save_settings
from flask import request, send_from_directory
from logging.handlers import RotatingFileHandler
from app_paths import get_resource_path, get_project_root, get_logs_dir

def resolve_frontend_dist():
    packaged_dist = get_resource_path("frontend_dist")
    if os.path.isdir(packaged_dist):
        return packaged_dist
    dev_dist = os.path.join(get_project_root(), "frontend", "dist")
    if os.path.isdir(dev_dist):
        return dev_dist
    return None

FRONTEND_DIST = resolve_frontend_dist()

app = flask.Flask(
    __name__,
    static_folder=FRONTEND_DIST if FRONTEND_DIST else None,
    static_url_path=""
)
CORS(app)

logger = logging.getLogger("todolist.server")
logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler(
    f"{get_logs_dir()}/backend.log", maxBytes=1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

SQLinit("tasks")
storage = SQLStorage("tasks") 
print("server.py loaded!")


@app.route("/api/", methods=["POST"])
def index():
    return "Welcome to the To-Do List API!"

@app.route("/api/add", methods=["POST"])
def add_task():
    if request.is_json:
        data = flask.request.json
        description = data.get("description", "")
        details = data.get("details", "")
        due_date = data.get("due_date", None)
        category = data.get("category", "personal")
        priority = data.get("priority", "medium")
        color = data.get("color", None)
    else:
        description = request.args.get("description")
        details = request.args.get("details")
        due_date = request.args.get("due_date")
        category = request.args.get("category", "personal")
        priority = request.args.get("priority", "medium")
        color = request.args.get("color")
    
    task = {
        "description": description,
        "details": details,
        "completed": False,
        "due_date": due_date,
        "category": category,
        "priority": priority,
        "color": color
    }

    task_id = storage.add_task(task)
    return flask.jsonify({"task_id": task_id})

@app.route("/api/list", methods=["GET"])
def list_tasks():
    try:
        tasks = storage.list_task_flasks()
        if tasks is None:
            return flask.jsonify("No tasks found"), 404
        return flask.jsonify({"tasks": tasks})
    except Exception as exc:
        logger.error(f"List tasks failed: {exc}\n{traceback.format_exc()}")
        return flask.jsonify({"error": "Failed to list tasks"}), 500

@app.route("/api/done", methods=["POST"])
def done_task():
    if request.is_json:
        data = flask.request.json or {}
        task_id = data.get("id")
    else:
        task_id = request.args.get("id")

    if task_id is None:
        return flask.jsonify({"error": "Task ID is required"}), 400

    success = storage.done_task(task_id)
    if not success:
        return flask.jsonify({"error": "Task not found"}), 404

    return flask.jsonify({"message": f"Task {task_id} marked as done"})

@app.route("/api/remove", methods=["POST"])
def remove_task():
    if request.is_json:
        data = flask.request.json or {}
        task_id = data.get("id")
    else:
        task_id = request.args.get("id")

    if task_id is None:
        return flask.jsonify({"error": "Task ID is required"}), 400

    success = storage.remove_task(task_id)
    if not success:
        return flask.jsonify({"error": "Task not found"}), 404

    return flask.jsonify({"message": f"Task {task_id} removed"})

@app.route("/api/reopen", methods=["POST"])
def reopen_task():
    if request.is_json:
        data = flask.request.json or {}
        task_id = data.get("id")
    else:
        task_id = request.args.get("id")

    if task_id is None:
        return flask.jsonify({"error": "Task ID is required"}), 400

    success = storage.reopen_task(task_id)
    if not success:
        return flask.jsonify({"error": "Task not found"}), 404

    return flask.jsonify({"message": f"Task {task_id} reopened"})

@app.route("/api/update", methods=["POST"])
def update_task():
    if request.is_json:
        data = flask.request.json or {}
        task_id = data.get("id")
        description = data.get("description", "")
        details = data.get("details", "")
        due_date = data.get("due_date", None)
        category = data.get("category", "personal")
        priority = data.get("priority", "medium")
        color = data.get("color", None)
    else:
        task_id = request.args.get("id")
        description = request.args.get("description", "")
        details = request.args.get("details", "")
        due_date = request.args.get("due_date")
        category = request.args.get("category", "personal")
        priority = request.args.get("priority", "medium")
        color = request.args.get("color")

    if task_id is None:
        return flask.jsonify({"error": "Task ID is required"}), 400

    success = storage.update_task(task_id, description, details, due_date, category, priority, color)
    if not success:
        return flask.jsonify({"error": "Task not found"}), 404

    return flask.jsonify({"message": f"Task {task_id} updated"})


@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    if request.method == "GET":
        return flask.jsonify(load_settings())

    if request.is_json:
        data = flask.request.json or {}
        language = data.get("language", "en")
    else:
        language = request.args.get("language", "en")

    if language not in ("en", "zh"):
        return flask.jsonify({"error": "Invalid language"}), 400

    save_settings({"language": language})
    return flask.jsonify({"language": language})

if FRONTEND_DIST:
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path.startswith("api"):
            return flask.jsonify({"error": "Not found"}), 404
        full_path = os.path.join(FRONTEND_DIST, path)
        if path and os.path.isfile(full_path):
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled error: {error}\n{traceback.format_exc()}")
    return flask.jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)
