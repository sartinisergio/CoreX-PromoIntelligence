@echo off
echo ========================================
echo   CoreX - Scarica aggiornamenti da GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo Scaricamento modifiche...
git pull origin main

echo.
echo ========================================
echo   Completato!
echo ========================================
pause