@echo off
cd /d "E:\git\katalon-dashboard"
call ".venv\Scripts\activate.bat"
python scripts\parse_and_send.py >> "scripts\sync.log" 2>&1
