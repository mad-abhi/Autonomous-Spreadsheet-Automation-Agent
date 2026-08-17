@echo off
title Autonomous Spreadsheet Automation Agent
echo Starting backend server on http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause