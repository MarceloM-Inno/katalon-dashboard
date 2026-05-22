@echo off
cd /d "E:\Victor\Dashboard\katalon-dashboard\scripts"
python parse_and_send.py >> "sync.log" 2>&1
