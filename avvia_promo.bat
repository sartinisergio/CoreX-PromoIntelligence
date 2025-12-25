@echo off
cd /d %~dp0
call venv\Scripts\activate
streamlit run webapp.py --server.port 8502