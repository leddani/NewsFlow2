@echo off
title NewsFlow AI Editor - PERMANENT MODE
color 0A

echo.
echo ====================================
echo   NEWSFLOW AI EDITOR - 24/7 MODE
echo ====================================
echo.
echo [INFO] Duke startuar platformen...
echo [INFO] Kjo dritare duhet te mbetet e hapur!
echo.
echo [CTRL+C] per te ndalur
echo.

cd /d "%~dp0"

:restart_loop
echo.
echo [%date% %time%] NEWSFLOW AI EDITOR - PERMANENT MODE
echo ===============================================================
echo [%date% %time%] 10 Website ne monitoring
echo [%date% %time%] LLM Processing aktiv
echo [%date% %time%] Telegram Bot ne pritje  
echo [%date% %time%] Scheduler i vazhdueshëm
echo ===============================================================

REM Ndaloj proceset e vjetra python per te shmangur konfliktet e port
echo [%date% %time%] Duke ndalur proceset e vjetra...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [%date% %time%] Duke startuar backend...
echo.

python start_backend.py

echo.
echo [%date% %time%] Backend u ndal!
echo.
echo Doni te ristartohet sistemi? (Y/N)
set /p restart="Vendosni Y per ristart, N per dalje: "

if /i "%restart%"=="Y" (
    echo Duke ristartur ne 3 sekonda...
    timeout /t 3 /nobreak >nul
    goto restart_loop
) else (
    echo Sistemi po mbyllet...
    pause
    exit
) 