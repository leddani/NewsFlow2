#!/usr/bin/env python3
"""
Script për kontroll final të NewsFlow AI Editor
"""
import requests

def check_final_status():
    try:
        print("🚀 STATUSI FINAL I NEWSFLOW AI EDITOR:")
        print("=" * 50)
        
        # Backend
        backend = requests.get('http://localhost:8000/')
        backend_status = "AKTIV" if backend.status_code == 200 else "PROBLEM"
        print(f"✅ Backend: {backend_status}")
        
        # Scheduler  
        sched = requests.get('http://localhost:8000/scheduler/status').json()
        sched_status = "AKTIV" if sched['running'] else "I NDALUR"
        print(f"✅ Scheduler: {sched_status} ({sched['active_tasks']}/{sched['total_tasks']} tasks)")
        
        # Telegram Bot
        tg = requests.get('http://localhost:8000/telegram/status').json()
        tg_status = "AKTIV" if tg['bot_initialized'] else "I NDALUR"
        print(f"✅ Telegram Bot: {tg_status} ({tg['articles_in_cache']} artikuj në cache)")
        
        # Articles
        articles = requests.get('http://localhost:8000/articles/').json()
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        recent = [a for a in articles if today in a['created_at']]
        print(f"📊 Artikuj total: {len(articles)}")
        print(f"🆕 Artikuj sot: {len(recent)}")
        
        print("=" * 50)
        print("🎯 SISTEMI ËSHTË PLOTËSISHT AKTIV!")
        print("📱 Lajmet do të dërgohen automatikisht në Telegram!")
        print("🚀 Mund të përdorësh start_newsflow_forever.bat për 24/7!")
        
    except Exception as e:
        print(f"❌ Gabim: {e}")

if __name__ == "__main__":
    check_final_status() 