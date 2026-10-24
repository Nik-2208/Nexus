@echo off
REM NEXUS: Launch Streamlit application bound strictly to loopback (127.0.0.1)
echo Starting NEXUS AI Failure Intelligence Engine on loopback (127.0.0.1:8501)...
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
