@echo off
pyinstaller --noconsole --windowed --name TodoList --icon todolist_win.ico --add-data "todolist_win.ico;todolist_win.ico" --add-data "backend/cores/frontend_dist;frontend_dist" backend/cores/tray_app.py
