@echo off
cd /d "C:\Users\SARTINI\Desktop\CoreX_promo_intelligence"

echo Controllo modifiche in corso...

git add -A
git diff --cached --quiet

if %errorlevel%==0 (
    echo Nessuna modifica da caricare.
) else (
    for /f "tokens=1-3 delims=/" %%a in ('date /t') do set data=%%a-%%b-%%c
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set ora=%%a.%%b
    
    git commit -m "Aggiornamento %data% %ora%"
    git push origin main && echo Push completato con successo! || echo Errore durante il push.
)

pause
