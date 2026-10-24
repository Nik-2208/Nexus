@echo off
REM Launch NEXUS FastAPI Modern Web Application on Loopback (127.0.0.1:8000)
echo Starting NEXUS Web Server on http://127.0.0.1:8000 ...
python -m uvicorn nexus.web.server:app --host 127.0.0.1 --port 8000
