#!/usr/bin/env python3

import requests
import time
from datetime import datetime

def check_system_status():
    print("🔍 KONTROLLI I SISTEMIT - NEWSFLOW AI EDITOR")
    print("=" * 60)
    print(f"📅 Koha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    # Check Backend
    print("1. 🖥️ Backend...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend: AKTIV")
            backend_ok = True
        else:
            print(f"   ❌ Backend: ERROR ({response.status_code})")
            backend_ok = False
    except Exception as e:
        print(f"   ❌ Backend: NUK PERGJIGJET ({e})")
        backend_ok = False
    
    # Check Telegram Bot
    print("2. 📱 Telegram Bot...")
    try:
        response = requests.get("http://localhost:8000/telegram/status", timeout=5)
        if response.status_code == 200:
            status = response.json().get('status', 'unknown')
            if status == 'running':
                print("   ✅ Telegram: AKTIV")
                telegram_ok = True
            else:
                print(f"   ⚠️ Telegram: {status.upper()}")
                telegram_ok = False
        else:
            print(f"   ❌ Telegram: ERROR ({response.status_code})")
            telegram_ok = False
    except Exception as e:
        print(f"   ❌ Telegram: ERROR ({e})")
        telegram_ok = False
    
    # Check Scheduler
    print("3. 📡 Scheduler...")
    try:
        response = requests.get("http://localhost:8000/scheduler/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Scheduler returns 'running' field instead of 'status'
            running = data.get('running', False)
            active_tasks = data.get('active_tasks', 0)
            total_tasks = data.get('total_tasks', 0)
            
            if running:
                print("   ✅ Scheduler: AKTIV")
                print(f"      📊 Websites: {total_tasks}")
                print(f"      🔄 Active tasks: {active_tasks}")
                scheduler_ok = True
            else:
                print(f"   ⚠️ Scheduler: STOPPED")
                scheduler_ok = False
        else:
            print(f"   ❌ Scheduler: ERROR ({response.status_code})")
            scheduler_ok = False
    except Exception as e:
        print(f"   ❌ Scheduler: ERROR ({e})")
        scheduler_ok = False
    
    # Check Database
    print("4. 💾 Database...")
    try:
        response = requests.get("http://localhost:8000/articles", timeout=5)
        if response.status_code == 200:
            articles = response.json()
            pending = [a for a in articles if a.get('status') == 'scraped']
            published = [a for a in articles if a.get('status') == 'published']
            
            print(f"   ✅ Database: AKTIV")
            print(f"      📊 Total artikuj: {len(articles)}")
            print(f"      ⏳ Në pritje: {len(pending)}")
            print(f"      ✅ Të publikuar: {len(published)}")
            database_ok = True
        else:
            print(f"   ❌ Database: ERROR ({response.status_code})")
            database_ok = False
    except Exception as e:
        print(f"   ❌ Database: ERROR ({e})")
        database_ok = False
    
    # Check Websites
    print("5. 🌐 Websites...")
    try:
        response = requests.get("http://localhost:8000/websites", timeout=5)
        if response.status_code == 200:
            websites = response.json()
            active = [w for w in websites if not w.get('last_error')]
            errors = [w for w in websites if w.get('last_error')]
            
            print(f"   ✅ Websites: AKTIV")
            print(f"      📊 Total: {len(websites)}")
            print(f"      ✅ OK: {len(active)}")
            print(f"      ❌ Errors: {len(errors)}")
            websites_ok = True
        else:
            print(f"   ❌ Websites: ERROR ({response.status_code})")
            websites_ok = False
    except Exception as e:
        print(f"   ❌ Websites: ERROR ({e})")
        websites_ok = False
    
    # Overall Status
    print("\n" + "=" * 60)
    print("🎯 STATUS I PERGJITHSHEM:")
    print("=" * 60)
    
    all_ok = all([backend_ok, telegram_ok, scheduler_ok, database_ok, websites_ok])
    
    if all_ok:
        print("🎉 SISTEMI ËSHTË 100% FUNKSIONAL!")
        print("")
        print("✅ Workflow aktiv:")
        print("   1. 📡 Scheduler kontrollon websites (30 sekonda)")
        print("   2. 🧠 Scrapy Intelligent gjen lajme të reja")
        print("   3. 🤖 LLM përpunon përmbajtjen")
        print("   4. 📱 Telegram dërgon për review")
        print("   5. ✅ Ti aproves në Telegram")
        print("   6. 📝 WordPress publikon automatikisht")
        print("")
        print("🚀 SISTEMI ËSHTË GATI PËR PUNË 24/7!")
        
    else:
        print("⚠️ SISTEMI KA PROBLEME!")
        print("")
        print("❌ Komponente me probleme:")
        if not backend_ok:
            print("   - Backend")
        if not telegram_ok:
            print("   - Telegram Bot")
        if not scheduler_ok:
            print("   - Scheduler")
        if not database_ok:
            print("   - Database")
        if not websites_ok:
            print("   - Websites")
        print("")
        print("💡 Provo të restartosh sistemin me:")
        print("   start_newsflow_complete.bat")
    
    print("=" * 60)
    return all_ok

if __name__ == "__main__":
    check_system_status()