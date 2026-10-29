@echo off
cd /d "%~dp0"
start /min python -m uvicorn app:app --port 8000
start /min python worker_bot.py
exit