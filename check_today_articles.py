#!/usr/bin/env python3
"""
Script për të kontrolluar artikujt e sotëm
"""
import requests
from datetime import datetime

def check_today_articles():
    try:
        print("📊 Duke kontrolluar artikujt e sotëm...")
        
        # Get articles
        response = requests.get('http://localhost:8000/articles/')
        articles = response.json()
        
        # Filter today's articles
        today = datetime.now().strftime('%Y-%m-%d')
        recent_articles = [a for a in articles if today in a['created_at']]
        
        print(f"📈 Artikuj total: {len(articles)}")
        print(f"🆕 Artikuj sot ({today}): {len(recent_articles)}")
        
        if recent_articles:
            print("\n📋 Artikujt e sotëm:")
            for i, article in enumerate(recent_articles[:5], 1):
                title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
                print(f"   {i}. {title}")
                print(f"      Status: {article['status']} | Created: {article['created_at'][:19]}")
        else:
            print("⚠️  Nuk ka artikuj të rinj sot")
            
        # Check scheduler status
        sched_response = requests.get('http://localhost:8000/scheduler/status')
        sched_status = sched_response.json()
        print(f"\n🔄 Scheduler: {'AKTIV' if sched_status['running'] else 'I NDALUR'}")
        print(f"📡 Tasks aktive: {sched_status['active_tasks']}/{sched_status['total_tasks']}")
        
    except Exception as e:
        print(f"❌ Gabim: {e}")

if __name__ == "__main__":
    check_today_articles() 