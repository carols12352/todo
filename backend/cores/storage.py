import json
import os
import logging
from logging.handlers import RotatingFileHandler

#initialize logger
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

#create a file if DNE
class Storage:
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        self.path = os.path.join(base_dir, "data", "task.json")
        os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w") as file:
                json.dump([], file)
        with open(self.path,"r") as f:
            try:
                self.tasklist = json.load(f)
                logger.debug("Tasks loaded successfully")
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON")
                self.tasklist = []

    def get_tasks(self):
        logger.debug("Retriving tasks")
        return self.tasklist
    
    def save_tasks(self, tasklist):
        with open(self.path, "w") as f:
            json.dump(tasklist, f, indent=4)
        logger.debug("Tasks saved successfully")

    def add_task(self,task):
        try:
            data = json.loads(task)
            self.tasklist.append(data)
        except json.JSONDecodeError:
            logger.error("Invalid task format")
            return
        logger.debug(f"Task added: {task}")
        self.save_tasks(self.tasklist)
        return
    
    def list_tasks(self):
        if not self.tasklist:
            print("No tasks found.")
            return
        for task in self.tasklist:
            print(task["id"], task["description"], task["details"], task["completed"], task["due_date"],)
        logger.debug("Listed all tasks")
        return
    
    def remove_task(self, task_id):
        new_tasks = [t for t in self.tasklist if t.get("id") != task_id]

        if len(new_tasks) == len(self.tasklist):
            print(f"Task ID {task_id} not found.")
            logger.warning(f"Task ID {task_id} not found for removal")
            return False

        self.tasklist = new_tasks
        self.save_tasks(self.tasklist)

        print(f"Task ID {task_id} removed.")
        logger.debug(f"Task removed successfully: ID={task_id}")
        return True
    
    def done_task(self, task_id):
        for task in self.tasklist:
            if task.get("id") == task_id:
                task["completed"] = True
                self.save_tasks(self.tasklist)
                logger.debug(f"Task marked as done: ID={task_id}")
                print(f"Task ID {task_id} marked as done.")
                return True
        logger.warning(f"Task ID {task_id} not found to mark as done")
        print(f"Task ID {task_id} not found.")
        return False

    



        

