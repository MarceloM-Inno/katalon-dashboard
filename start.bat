@echo off
cd /d "%~dp0"
streamlit run Graficos.py --server.port 8501 --server.headless true
pause
