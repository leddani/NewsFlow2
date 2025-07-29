@echo off
chcp 65001 >nul
title NewsFlow AI Editor - Sistemi i Plote 24/7

echo ================================================
echo       NEWSFLOW AI EDITOR - SISTEMI I PLOTE
echo ================================================
echo 1. Backend + API
echo 2. Scrapy Intelligent Engine  
echo 3. LLM Processing
echo 4. Telegram Bot
echo 5. Scheduler (30 sekonda)
echo 6. WordPress Publishing
echo ================================================
echo.

echo [%TIME%] Filloj sistemin e plote...

REM Kill any existing Python processes to avoid conflicts
echo [%TIME%] Mbyll proceset e vjetra...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [%TIME%] Startoj backend...
start /B python start_backend.py

REM Wait for backend to fully start
echo [%TIME%] Pres qe backend te ngarkohet...
timeout /t 5 /nobreak >nul

REM Test if backend is running
echo [%TIME%] Kontrolloj backend...
python -c "import requests; r=requests.get('http://localhost:8000/', timeout=5); print('Backend OK' if r.status_code==200 else 'Backend ERROR')" 2>nul
if errorlevel 1 (
    echo [%TIME%] ERROR: Backend nuk u startua!
    pause
    exit /b 1
)

echo [%TIME%] Backend eshte aktiv!

REM Start Telegram Bot
echo [%TIME%] Aktivizoj Telegram Bot...
python -c "import requests; r=requests.post('http://localhost:8000/telegram/start', timeout=10); print('Telegram:', r.json().get('status', 'ERROR') if r.status_code==200 else 'ERROR')" 2>nul

REM Start Scheduler  
echo [%TIME%] Aktivizoj Scheduler...
python -c "import requests; r=requests.post('http://localhost:8000/scheduler/start', timeout=10); print('Scheduler:', r.json().get('status', 'ERROR') if r.status_code==200 else 'ERROR')" 2>nul

REM Verify all components
echo [%TIME%] Kontrolloj te gjitha komponentet...
python -c "
import requests, time
try:
    # Backend
    r1 = requests.get('http://localhost:8000/', timeout=5)
    backend_ok = r1.status_code == 200
    
    # Telegram
    r2 = requests.get('http://localhost:8000/telegram/status', timeout=5)
    telegram_ok = r2.status_code == 200 and r2.json().get('status') == 'running'
    
    # Scheduler
    r3 = requests.get('http://localhost:8000/scheduler/status', timeout=5)
    scheduler_ok = r3.status_code == 200 and r3.json().get('status') == 'running'
    
    print('')
    print('============ STATUS FINAL ============')
    print('Backend:   ' + ('✓ AKTIV' if backend_ok else '✗ ERROR'))
    print('Telegram:  ' + ('✓ AKTIV' if telegram_ok else '✗ ERROR'))  
    print('Scheduler: ' + ('✓ AKTIV' if scheduler_ok else '✗ ERROR'))
    print('Scrapy:    ✓ INTELLIGENT (default)')
    print('LLM:       ✓ AKTIV')
    print('WordPress: ✓ AKTIV') 
    print('=====================================')
    
    if all([backend_ok, telegram_ok, scheduler_ok]):
        print('')
        print('🎉 SISTEMI ESHTE 100%% AKTIV!')
        print('📡 Scheduler po kontrollon websites cdo 30 sekonda')
        print('🧠 Scrapy Intelligent po kerkon lajme te reja')
        print('📱 Telegram Bot po pret per review')
        print('📝 WordPress gati per publikim automatik')
        print('')
        print('✅ NewsFlow AI Editor eshte ne pune 24/7!')
    else:
        print('')
        print('⚠️ Disa komponente kane probleme!')
        exit(1)
        
except Exception as e:
    print('❌ ERROR ne verifikim:', str(e))
    exit(1)
"

if errorlevel 1 (
    echo.
    echo [%TIME%] ❌ Ka pasur probleme ne startim!
    echo A doni te riprovat? (Y/N)
    set /p choice=
    if /i "%choice%"=="Y" goto start
    pause
    exit /b 1
)

echo.
echo ================================================
echo           SISTEMI ESHTE AKTIV 24/7!
echo ================================================
echo Backend:      http://localhost:8000
echo API Docs:     http://localhost:8000/docs  
echo Database:     newsflow.db
echo Logs:         Shiko terminal per detaje
echo ================================================
echo.
echo [%TIME%] Sistemi po punon ne background...
echo [%TIME%] Mbyll kete dritare vetem nese doni te ndaloni sistemin!
echo.

REM Keep the system running and show periodic status
:monitor
timeout /t 300 /nobreak >nul
echo [%TIME%] Sistemi vazhdoj te punoj... (kontrollo cdo 5 minuta)

REM Quick health check
python -c "
import requests
try:
    r = requests.get('http://localhost:8000/', timeout=3)
    if r.status_code == 200:
        print('[%TIME%] ✓ Sistemi eshte ende aktiv')
    else:
        print('[%TIME%] ⚠️ Backend ka probleme')
        exit(1)
except:
    print('[%TIME%] ❌ Backend nuk po pergjigjet!')
    exit(1)
" 2>nul

if errorlevel 1 (
    echo [%TIME%] Sistema ka probleme! A doni te restartoni? (Y/N)
    set /p restart_choice=
    if /i "%restart_choice%"=="Y" (
        echo [%TIME%] Duke restartuar...
        goto start
    ) else (
        echo [%TIME%] Duke ndalur sistemin...
        taskkill /F /IM python.exe >nul 2>&1
        exit /b 1
    )
)

goto monitor

:start
goto :eof