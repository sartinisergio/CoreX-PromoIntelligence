@echo off
title CoreX - Core Extractor
cd /d C:\Users\SARTINI\Desktop\CoreX
call venv\Scripts\activate.bat
streamlit run webapp.py
pause