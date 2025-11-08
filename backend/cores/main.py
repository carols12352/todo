"""
程序开始：
  读取 tasks.json
  如果没有则创建空列表

循环：
  让用户输入命令
  如果命令是 add → 添加任务
  如果命令是 list → 显示任务
  如果命令是 done → 修改状态
  如果命令是 remove → 删除
  如果命令是 exit → 保存并退出

程序结束：
  保存任务列表

json 格式：
[
{
"id":1,
"description":"Buy groceries",
"completed":false
"due_date":"2024-06-30"
"details":"Remember to buy milk, eggs, and bread."
},
}]
"""


from storage import Storage


def main():
    while True:
        storage = Storage()
        input_cmd = input("Command (add/list/done/remove/exit): ").strip().lower()
        if(input == "exit"):
            storage.save_tasks(storage.get_tasks())
            print("Tasks saved. Exiting.")
            break
        elif(input_cmd == "add"):
            id = input("Task ID: ")
            description = input("Description: ")
            details = input("Details: ")
            due_date = input("Due Date (YYYY-MM-DD): ")
            task = f'''
            {{
                "id": {id},
                "description": "{description}",
                "completed": false,
                "due_date": "{due_date}",
                "details": "{details}"
            }}
            '''
            storage.add_task(task)
        elif(input_cmd == "list"):
            storage.list_tasks()
        elif(input_cmd == "done"):
            task_id = input("Enter Task ID to mark as done: ")
            storage.done_task(int(task_id))
        elif(input_cmd == "remove"):
            task_id = input("Enter Task ID to remove: ")
            storage.remove_task(int(task_id))
        elif(input_cmd == "exit"):
            storage.save_tasks(storage.get_tasks())
            print("Tasks saved. Exiting.")
            break
        else:
            print("Invalid command. Please try again.")

if __name__ == "__main__":
    main()