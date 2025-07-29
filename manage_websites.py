#!/usr/bin/env python3
"""
CLI tool për menaxhimin e website-ve në NewsFlow AI Editor.

Usage:
    python manage_websites.py list
    python manage_websites.py add
    python manage_websites.py start
    python manage_websites.py stop
    python manage_websites.py status
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def list_websites():
    """List all websites."""
    print("📋 WEBSITE-T E KONFIGURUAR")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/websites")
        if response.status_code == 200:
            websites = response.json()
            
            if not websites:
                print("❌ Nuk ka website të konfiguruar.")
                print("💡 Përdor: python manage_websites.py add")
                return
            
            for website in websites:
                status_icon = "🟢" if website["active"] else "🔴"
                last_scraped = website.get("last_scraped", "Asnjëherë")
                if last_scraped and last_scraped != "Asnjëherë":
                    last_scraped = last_scraped[:19].replace('T', ' ')
                
                print(f"{status_icon} [{website['id']}] {website['name']}")
                print(f"   🔗 {website['url']}")
                print(f"   ⏱️  Interval: {website['scrape_interval_minutes']} min")
                print(f"   📰 Articles: {website.get('total_articles_scraped', 0)}")
                print(f"   🕐 Last: {last_scraped}")
                
                if website.get("last_error"):
                    print(f"   ❌ Error: {website['last_error'][:100]}...")
                
                if website.get("error_count", 0) > 0:
                    print(f"   ⚠️  Errors: {website['error_count']}")
                print()
                
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def add_website():
    """Add a new website interactively."""
    print("📝 SHTIMI I WEBSITE TË RI")
    print("-" * 30)
    
    # Get input from user
    name = input("Emri i website: ").strip()
    if not name:
        print("❌ Emri është i detyrueshëm!")
        return
    
    url = input("URL (me https://): ").strip()
    if not url:
        print("❌ URL është i detyrueshëm!")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    interval_input = input("Interval në minuta (default 5): ").strip()
    try:
        interval = int(interval_input) if interval_input else 5
        if interval < 1:
            interval = 5
    except ValueError:
        interval = 5
    
    active_input = input("Aktiv menjëherë? (y/n, default y): ").strip().lower()
    active = active_input != 'n'
    
    website_data = {
        "name": name,
        "url": url,
        "scrape_interval_minutes": interval,
        "active": active
    }
    
    print(f"\n🔄 Duke shtuar website...")
    print(f"   Emri: {name}")
    print(f"   URL: {url}")
    print(f"   Interval: {interval} min")
    print(f"   Aktiv: {'Po' if active else 'Jo'}")
    
    try:
        response = requests.post(f"{BASE_URL}/websites", json=website_data)
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ {result['message']}")
            print(f"   ID: {result['website']['id']}")
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"\n❌ Connection error: {e}")

def start_scheduler():
    """Start the automatic scheduler."""
    print("🚀 STARTIMI I SCHEDULER")
    print("-" * 25)
    
    try:
        response = requests.post(f"{BASE_URL}/scheduler/start")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            print("💡 Sistemi tani do të scrape automatikisht website-t!")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def stop_scheduler():
    """Stop the automatic scheduler."""
    print("⏹️ NDALIMI I SCHEDULER")
    print("-" * 25)
    
    try:
        response = requests.post(f"{BASE_URL}/scheduler/stop")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def show_status():
    """Show scheduler and system status."""
    print("📊 STATUS I SISTEMIT")
    print("-" * 25)
    
    # Scheduler status
    try:
        response = requests.get(f"{BASE_URL}/scheduler/status")
        if response.status_code == 200:
            status = response.json()
            print(f"🔄 Scheduler: {'AKTIV' if status['running'] else 'JOAKTIV'}")
            print(f"📋 Active Tasks: {status['active_tasks']}")
            print(f"📈 Total Tasks: {status['total_tasks']}")
        else:
            print(f"❌ Scheduler Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Scheduler Connection Error: {e}")
    
    print()
    
    # Websites summary
    try:
        response = requests.get(f"{BASE_URL}/websites")
        if response.status_code == 200:
            websites = response.json()
            active_count = sum(1 for w in websites if w.get('active', False))
            total_articles = sum(w.get('total_articles_scraped', 0) for w in websites)
            
            print(f"🌐 Total Websites: {len(websites)}")
            print(f"🟢 Active: {active_count}")
            print(f"🔴 Inactive: {len(websites) - active_count}")
            print(f"📰 Total Articles: {total_articles}")
        else:
            print(f"❌ Websites Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Websites Connection Error: {e}")

def quick_setup():
    """Quick setup with common Albanian news sites."""
    print("⚡ KONFIGURIMI I SHPEJTË")
    print("-" * 30)
    print("Do të shtohen disa website kryesore shqiptare:")
    print()
    
    common_sites = [
        {"name": "Top Channel", "url": "https://top-channel.tv/", "interval": 5},
        {"name": "Panorama", "url": "https://panorama.com.al/", "interval": 5},
        {"name": "Gazeta Shqip", "url": "https://gazeta-shqip.com/", "interval": 5},
        {"name": "Klan News", "url": "https://klankosova.tv/", "interval": 5},
        {"name": "RTK Live", "url": "https://rtklive.com/", "interval": 5}
    ]
    
    for site in common_sites:
        print(f"📝 {site['name']} - {site['url']}")
    
    confirm = input("\nShto këto website? (y/n): ").strip().lower()
    if confirm == 'y':
        added = 0
        for site in common_sites:
            try:
                website_data = {
                    "name": site["name"],
                    "url": site["url"],
                    "scrape_interval_minutes": site["interval"],
                    "active": True
                }
                
                response = requests.post(f"{BASE_URL}/websites", json=website_data)
                if response.status_code == 200:
                    print(f"✅ {site['name']}")
                    added += 1
                else:
                    print(f"❌ {site['name']} - Error {response.status_code}")
            except Exception as e:
                print(f"❌ {site['name']} - {e}")
        
        print(f"\n🎉 {added}/{len(common_sites)} website u shtuan!")
        if added > 0:
            print("💡 Tani mund të startosh scheduler: python manage_websites.py start")

def show_help():
    """Show help message."""
    print("🔧 NEWSFLOW WEBSITE MANAGER")
    print("=" * 40)
    print("Komanda të disponueshme:")
    print()
    print("📋 list       - Shiko të gjitha website-t")
    print("📝 add        - Shto website të ri")
    print("⚡ setup      - Konfigurimi i shpejtë")
    print("🚀 start      - Starto scheduler")
    print("⏹️ stop       - Ndalo scheduler")
    print("📊 status     - Shiko statusin")
    print("❓ help       - Shiko këtë ndihmë")
    print()
    print("Shembuj:")
    print("  python manage_websites.py list")
    print("  python manage_websites.py add")
    print("  python manage_websites.py setup")
    print("  python manage_websites.py start")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_websites()
    elif command == "add":
        add_website()
    elif command == "setup":
        quick_setup()
    elif command == "start":
        start_scheduler()
    elif command == "stop":
        stop_scheduler()
    elif command == "status":
        show_status()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Komandë e panjohur: {command}")
        print("💡 Përdor: python manage_websites.py help")

if __name__ == "__main__":
    main() 