import flask
from flask_cors import CORS
from storage import SQLStorage

app = flask.Flask(__name__)
CORS(app)

storage = SQLStorage("tasks") 
print("server.py loaded!")


@app.route("/api/", methods=["POST"])
def index():
    return "Welcome to the To-Do List API!"

@app.route("/api/add", methods=["POST"])
def add_task():
    data = flask.request.json
    description = data.get("description", "")
    details = data.get("details", "")
    due_date = data.get("due_date", None)
    
    task = {
        "description": description,
        "details": details,
        "completed": False,
        "due_date": due_date
    }

    task_id = storage.add_task(task)
    return flask.jsonify({"task_id": task_id})

@app.route("/api/list", methods=["GET"])
def list_tasks():
    tasks = storage.list_task_flasks()
    return flask.jsonify({"tasks": tasks})

@app.route("/api/done", methods=["POST"])
def done_task():
    data = flask.request.json or {}
    task_id = data.get("id")

    if task_id is None:
        return flask.jsonify({"error": "Task ID is required"}), 400

    success = storage.done_task(task_id)
    if not success:
        return flask.jsonify({"error": "Task not found"}), 404

    return flask.jsonify({"message": f"Task {task_id} marked as done"})

@app.route("/api/remove", methods=["POST"])
def remove_task():
    data = flask.request.json or {}
    task_id = data.get("id")

    if task_id is None:
        return flask.jsonify({"error": "Task ID is required"}), 400

    success = storage.remove_task(task_id)
    if not success:
        return flask.jsonify({"error": "Task not found"}), 404

    return flask.jsonify({"message": f"Task {task_id} removed"})

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)
