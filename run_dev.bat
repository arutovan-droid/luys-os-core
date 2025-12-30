@echo off
cd /d %~dp0
call .\.venv\Scripts\activate
python -m uvicorn api.main:app --host 127.0.0.1 --port 7777 --reload --ws wsproto
