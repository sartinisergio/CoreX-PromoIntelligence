@echo off
echo ========================================
echo   CoreX - Aggiornamento GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo Controllo modifiche...
git status

echo.
set /p messaggio="Messaggio commit (o INVIO per 'Aggiornamento automatico'): "
if "%messaggio%"=="" set messaggio=Aggiornamento automatico %date% %time%

echo.
echo Aggiunta file modificati...
git add -A

echo Commit...
git commit -m "%messaggio%"

echo Push su GitHub...
git push origin main

echo.
echo ========================================
echo   Completato!
echo ========================================
pause