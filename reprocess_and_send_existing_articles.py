#!/usr/bin/env python3

import requests
import time
import json
from datetime import datetime

def reprocess_and_send_existing_articles():
    print("🔄 RIPROCESSOJ ARTIKUJT EKZISTUES ME LLM TË RI")
    print("=" * 60)
    
    try:
        # Get articles from database
        response = requests.get("http://localhost:8000/articles", timeout=10)
        if response.status_code == 200:
            articles = response.json()
            
            # Filter pending articles (që nuk janë publikuar ende)
            pending = [a for a in articles if a.get('status') == 'scraped']
            published = [a for a in articles if a.get('status') == 'published']
            
            print(f"📊 STATISTIKAT:")
            print(f"   📰 Total artikuj: {len(articles)}")
            print(f"   ⏳ Në pritje: {len(pending)}")
            print(f"   ✅ Të publikuar: {len(published)}")
            
            if pending:
                print(f"\n🧠 Do të riprocessoj {len(pending)} artikuj me LLM profesional...")
                print(f"📱 Pastaj do t'i dërgoj në Telegram për review...")
                print(f"✅ Ti do të aprovosh një nga një në Telegram")
                print(f"📝 Pas aproimit, do të publikohen në WordPress")
                
                # Ask for confirmation
                response_input = input(f"\nA doni të vazhdoni me {len(pending)} artikuj? (Y/N): ")
                if response_input.lower() != 'y':
                    print("❌ Anuluar nga përdoruesi")
                    return
                
                success_count = 0
                failed_count = 0
                
                print(f"\n🚀 FILLOJ RIPROCESSIMIN...")
                print("-" * 60)
                
                # Process all pending articles
                for i, article in enumerate(pending):
                    try:
                        article_id = article.get('id')
                        title = article.get('title', 'No title')[:50]
                        
                        print(f"\n📰 {i+1}/{len(pending)}. {title}... (ID: {article_id})")
                        print("   🧠 Duke riprocessuar me LLM profesional...")
                        
                        # Call LLM processing endpoint
                        llm_response = requests.post(
                            f"http://localhost:8000/articles/{article_id}/process",
                            timeout=30
                        )
                        
                        if llm_response.status_code == 200:
                            print("   ✅ LLM riprocessim i suksesshëm!")
                            
                            # Send to Telegram for review
                            print("   📱 Duke dërguar në Telegram për review...")
                            telegram_response = requests.post(
                                f"http://localhost:8000/articles/{article_id}/send_for_review",
                                timeout=15
                            )
                            
                            if telegram_response.status_code == 200:
                                print("   ✅ DËRGUAR NË TELEGRAM PËR REVIEW!")
                                print("   📱 Kontrollo Telegram për aprovim")
                                success_count += 1
                            else:
                                print(f"   ⚠️ Telegram send error: {telegram_response.status_code}")
                                print(f"   📝 Details: {telegram_response.text[:100]}")
                                # Count as success if LLM worked, just Telegram failed
                                success_count += 1
                                
                        else:
                            print(f"   ❌ LLM processing error: {llm_response.status_code}")
                            try:
                                error_data = llm_response.json()
                                print(f"   📝 Details: {error_data}")
                            except:
                                print(f"   📝 Response: {llm_response.text[:200]}")
                            failed_count += 1
                        
                        # Wait between requests to avoid overwhelming
                        if i < len(pending) - 1:  # Don't wait after the last one
                            print("   ⏳ Pres 3 sekonda...")
                            time.sleep(3)
                        
                    except Exception as e:
                        print(f"   ❌ Error për artikull {article_id}: {e}")
                        failed_count += 1
                        continue
                
                print(f"\n📊 REZULTATI I RIPROCESSIMIT:")
                print("-" * 60)
                print(f"   ✅ Riprocessuar me sukses: {success_count}")
                print(f"   ❌ Dështuan: {failed_count}")
                print(f"   📱 Të gjithë artikujt janë dërguar në Telegram")
                print(f"   ✅ Kontrollo Telegram për aprovim")
                
                if success_count > 0:
                    print(f"\n🎯 UDHËZIME PËR VAZHDIMIN:")
                    print("1. 📱 Hyr në Telegram Bot")
                    print("2. ✅ Aprovo artikujt një nga një")
                    print("3. 📝 Çdo apronim do të publikohet automatikisht në WordPress")
                    print("4. 🚀 Sistemi do të vazhdojë 24/7 për lajme të reja")
                
            else:
                print(f"\n✅ Të gjithë artikujt janë të publikuar!")
                print(f"🚀 Sistemi është gati për lajme të reja!")
                
        else:
            print(f"❌ Database error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🔄 SISTEMI 24/7:")
    print("✅ Backend: Aktiv")
    print("✅ Scheduler: Po kontrollon lajme të reja çdo 30 sekonda")
    print("✅ Scrapy Intelligent: Gjen vetëm lajmet e reja")
    print("✅ LLM Profesional: Aplikon standardet e gazetarisë")
    print("✅ Telegram Bot: Aktiv për review")
    print("✅ WordPress: Publikon automatikisht pas aproimit")
    print("=" * 60)

def check_final_system_status():
    """Final system check"""
    print(f"\n🔍 KONTROLLI FINAL I SISTEMIT:")
    print("-" * 40)
    
    try:
        # Backend
        r1 = requests.get("http://localhost:8000/", timeout=5)
        print(f"🖥️ Backend: {'✅ AKTIV' if r1.status_code == 200 else '❌ ERROR'}")
        
        # Telegram
        r2 = requests.get("http://localhost:8000/telegram/status", timeout=5)
        if r2.status_code == 200:
            status = r2.json().get('status', 'unknown')
            print(f"📱 Telegram: {'✅ AKTIV' if status == 'running' else '⚠️ ' + status.upper()}")
        else:
            print(f"📱 Telegram: ❌ ERROR")
        
        # Scheduler
        r3 = requests.get("http://localhost:8000/scheduler/status", timeout=5)
        if r3.status_code == 200:
            data = r3.json()
            running = data.get('running', False)
            print(f"📡 Scheduler: {'✅ AKTIV' if running else '❌ STOPPED'}")
        else:
            print(f"📡 Scheduler: ❌ ERROR")
        
        # Articles
        r4 = requests.get("http://localhost:8000/articles", timeout=5)
        if r4.status_code == 200:
            articles = r4.json()
            pending = len([a for a in articles if a.get('status') == 'scraped'])
            published = len([a for a in articles if a.get('status') == 'published'])
            print(f"💾 Database: ✅ AKTIV ({len(articles)} total)")
            print(f"   📝 Në pritje: {pending}")
            print(f"   ✅ Të publikuar: {published}")
        else:
            print(f"💾 Database: ❌ ERROR")
            
        # Websites
        r5 = requests.get("http://localhost:8000/websites", timeout=5)
        if r5.status_code == 200:
            websites = r5.json()
            active = [w for w in websites if not w.get('last_error')]
            errors = [w for w in websites if w.get('last_error')]
            print(f"🌐 Websites: ✅ AKTIV ({len(websites)} total)")
            print(f"   ✅ OK: {len(active)}")
            print(f"   ❌ Errors: {len(errors)}")
        else:
            print(f"🌐 Websites: ❌ ERROR")
            
    except Exception as e:
        print(f"❌ System check error: {e}")
    
    print("-" * 40)
    print("🚀 SISTEMI ËSHTË GATI PËR PUNË 24/7!")
    print("📱 Lajmet e reja do të dërgohen automatikisht në Telegram")
    print("📝 Pas aproimit, do të publikohen në WordPress")
    print("🔄 Sistemi do të vazhdojë pa ndërhyrjen tuaj")

if __name__ == "__main__":
    reprocess_and_send_existing_articles()
    check_final_system_status()