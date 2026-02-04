# How to use
## Envrioment set up
First create your own virtual enviroment by using conda or just
```
python -m venv yourenvname
```
Then all the required dependencies are listed in `requirements.txt`
Simply install it using
```
pip install -r requirements.txt
```
## Server setup
### Frontend setup
The server is hosted using python flask, so simply cd to the cores directory in `backend/cores`
```
python server.py
```
The server should be up and running, should see output regarding the port and address of the server

### Backend setup
The server uses react and vite to run frontend, to start the server, simply just cd into `frontend` and then run
```
npm install
```
for depencencies(you only need once!) and use
```
npm run dev
```
to start the server.

## API calls 
The todo list implemented some basic features such as
- add: adds items to list and convert any valid date to DD-MM-YYYY to prevent further confusion
- list: returns the json of the current database and will display a message if no items in the list
- done: marks true for tasks after input the id
- remove: removes the task after input the id
### How to call API
as the flask server is hosted on 5000
we would call it using
```
127.0.0.1:5000/api/apiname
```
be aware that the api `add` `done` `remove` should have jsons posted to the method and list will just return the json format of the stuff inside.
to call `add` or `done` or `remove`, use the curl or other methods such as postman or just react axiom if you prefer.
here is the sample code for reference
```
curl.exe -X POST http://127.0.0.1:5000/api/add -H "Content-Type: application/json" -d '{ "description": "test", "details": "aaa", "due_date": "2025-11-12" }'
```
or for just id
```
curl -X POST http://127.0.0.1:5000/api/(done or remove) -H "Content-Type: application/json" -d '{\"id\": 5}'
```

## Packaging (PyInstaller + DMG)

### macOS
1. Build mac app (uses tray_app_mac.py):
   - `bash build_mac.sh`
2. Build DMG:
   - `bash dmg_mac.sh`
3. If cannot open the app on MacOS, Either:
   - Use
   ```
   sudo xattr -dr com.apple.quarantine /Applications/TodoList.app
   sudo xattr -dr com.apple.provenance /Applications/TodoList.app
   ```
   - Compile the app your self using the scripts

### Windows
1. Build windows app:
   - `build_win.bat`
