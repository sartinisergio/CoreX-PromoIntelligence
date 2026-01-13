@echo off
cd /d "C:\Users\SARTINI\Desktop\CoreX_promo_intelligence"

echo.
echo ========================================
echo    Aggiornamento GitHub in corso...
echo ========================================
echo.

git add -A

git commit -m "Aggiornamento %date% %time:~0,5%"

git push origin main

echo.
if %errorlevel%==0 (
    echo ========================================
    echo    Push completato con successo!
    echo ========================================
) else (
    echo ========================================
    echo    Errore durante il push
    echo ========================================
)

echo.
pause