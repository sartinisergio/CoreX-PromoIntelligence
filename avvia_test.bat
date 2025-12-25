@echo off
title CoreX TEST - Analisi Manuali
cd /d C:\Users\SARTINI\Desktop\CoreX_Test_Manuali
call C:\Users\SARTINI\Desktop\CoreX\venv\Scripts\activate.bat
streamlit run webapp.py --server.port 8502
pause