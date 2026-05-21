@echo off
cd /d "%~dp0"
call "C:\katalon-dashboard\.venv\Scripts\activate.bat"
python parse_and_send.py >> "C:\katalon-dashboard\scripts\sync.log" 2>&1
