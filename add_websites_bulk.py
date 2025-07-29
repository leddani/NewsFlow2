#!/usr/bin/env python3
"""
Script për shtimin masiv të website-ve shqiptare në NewsFlow AI Editor.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Lista e website-ve shqiptare për lajme
WEBSITES = [
    {
        "name": "Gazeta Express",
        "url": "https://www.gazetaexpress.com/",
        "scrape_interval_minutes": 7,
        "active": True
    },
    {
        "name": "RTSH News",
        "url": "https://www.rtsh.al/",
        "scrape_interval_minutes": 8,
        "active": True
    },
    {
        "name": "News24 Albania",
        "url": "https://news24.al/",
        "scrape_interval_minutes": 4,
        "active": True
    },
    {
        "name": "Koha Jone",
        "url": "https://kohajone.com/",
        "scrape_interval_minutes": 6,
        "active": True
    },
    {
        "name": "realitetipost",
        "url": "https://www.realitetipost.net/",
        "scrape_interval_minutes": 9,
        "active": True
    },
    {
        "name": "shkodrazone",
        "url": "https://shkodrazone.com/",
        "scrape_interval_minutes": 10,
        "active": True
    },
    {
        "name": "Balkan Web",
        "url": "https://www.balkanweb.com/",
        "scrape_interval_minutes": 5,
        "active": True
    },
    {
        "name": "Shekulli Online",
        "url": "https://shekulli.com.al/",
        "scrape_interval_minutes": 8,
        "active": True
    },
    {
        "name": "Reporter.al",
        "url": "https://www.reporter.al/",
        "scrape_interval_minutes": 6,
        "active": True
    },
    {
        "name": "Gazeta Panorama",
        "url": "https://www.panorama.com.al/",
        "scrape_interval_minutes": 7,
        "active": True
    }
]

def add_websites():
    """Add all websites to the system."""
    print("🌐 SHTIMI I WEBSITE-VE SHQIPTARE")
    print("=" * 50)
    
    added_count = 0
    failed_count = 0
    
    for i, website in enumerate(WEBSITES, 1):
        print(f"\n{i}. 📰 {website['name']}")
        print(f"   🔗 {website['url']}")
        print(f"   ⏱️  Interval: {website['scrape_interval_minutes']} min")
        
        try:
            response = requests.post(
                f"{BASE_URL}/websites",
                json=website,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Shtuar me sukses! (ID: {result.get('id', 'N/A')})")
                added_count += 1
            else:
                print(f"   ❌ Gabim: {response.status_code} - {response.text}")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ Gabim në connection: {str(e)}")
            failed_count += 1
            
        # Small delay between requests
        time.sleep(0.5)
    
    print(f"\n📊 PËRMBLEDHJE:")
    print(f"✅ Website të shtuar: {added_count}")
    print(f"❌ Dështime: {failed_count}")
    print(f"📝 Total: {len(WEBSITES)}")
    
    if added_count > 0:
        print(f"\n🎯 HAPE SWAGGER UI: http://localhost:8000/docs")
        print(f"📋 Kontroll website-t: GET /websites")
        print(f"🚀 Start scheduler: POST /scheduler/start")

if __name__ == "__main__":
    add_websites() 