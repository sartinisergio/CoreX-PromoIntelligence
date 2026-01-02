@echo off
cd /d "C:\Users\SARTINI\Desktop\CoreX_promo_intelligence"

echo Controllo modifiche in corso...

git add -A
git diff --cached --quiet

if %errorlevel%==0 (
    echo Nessuna modifica da caricare.
) else (
    git commit -m "Aggiornamento %date% %time:~0,5%"
    git push origin main && echo Push completato con successo! || echo Errore durante il push.
)

pause
