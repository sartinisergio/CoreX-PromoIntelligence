@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     CoreX - GitHub Auto-Update Script                     ║
echo ║     Zanichelli Promo Intelligence                         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: Verifica se siamo in una repo git
if not exist ".git" (
    echo [ERRORE] Questa cartella non è una repository Git!
    echo Esegui prima: git init
    pause
    exit /b 1
)

:: Mostra stato attuale
echo [INFO] Stato attuale della repository:
echo ----------------------------------------
git status --short
echo ----------------------------------------
echo.

:: Chiedi conferma
set /p CONFERMA="Vuoi procedere con il commit e push? (S/N): "
if /i not "%CONFERMA%"=="S" (
    echo [INFO] Operazione annullata.
    pause
    exit /b 0
)

:: Chiedi messaggio commit
echo.
set /p MSG="Inserisci messaggio commit (o premi INVIO per default): "

:: Se vuoto, usa messaggio default con timestamp
if "%MSG%"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATA=%%c-%%b-%%a
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set ORA=%%a:%%b
    set MSG=Update !DATA! !ORA! - Auto commit
)

echo.
echo [1/4] Aggiunta file modificati...
git add -A
if errorlevel 1 (
    echo [ERRORE] git add fallito!
    pause
    exit /b 1
)

echo [2/4] Creazione commit...
git commit -m "%MSG%"
if errorlevel 1 (
    echo [WARN] Nessuna modifica da committare o errore commit.
    echo        Potrebbe essere normale se non ci sono modifiche.
)

echo [3/4] Pull eventuali modifiche remote...
git pull --rebase origin main 2>nul || git pull --rebase origin master 2>nul
if errorlevel 1 (
    echo [WARN] Pull fallito, potrebbe essere il primo push.
)

echo [4/4] Push su GitHub...
git push origin main 2>nul || git push origin master 2>nul
if errorlevel 1 (
    echo [ERRORE] Push fallito!
    echo.
    echo Possibili cause:
    echo - Repository remota non configurata
    echo - Credenziali GitHub non valide
    echo - Branch non esiste
    echo.
    echo Prova: git remote add origin https://github.com/sartinisergio/CoreX-PromoIntelligence.git
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  ✓ COMPLETATO! Repository aggiornata su GitHub            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Commit: %MSG%
echo.

:: Mostra ultimo commit
echo [INFO] Ultimo commit:
git log -1 --oneline
echo.

pause