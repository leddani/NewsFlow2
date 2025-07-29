#!/usr/bin/env python3
"""
Script për të kontrolluar website-et e regjistruara
"""
import requests
from datetime import datetime

def check_websites():
    try:
        print("🌐 Duke kontrolluar website-et...")
        
        response = requests.get('http://localhost:8000/websites/')
        websites = response.json()
        
        print(f"📊 Website total: {len(websites)}")
        
        active_sites = [w for w in websites if w['active']]
        print(f"✅ Website aktive: {len(active_sites)}")
        
        print(f"\n📋 Lista e website-ve:")
        for i, site in enumerate(websites, 1):
            status = "🟢 AKTIV" if site['active'] else "🔴 I NDALUR"
            last_scraped = site.get('last_scraped', 'Never')[:19] if site.get('last_scraped') else 'Never'
            
            print(f"   {i}. {site.get('name', 'Unknown')} - {status}")
            print(f"      URL: {site.get('url', 'N/A')}")
            print(f"      Last scraped: {last_scraped}")
            
            if site.get('last_error'):
                error = site['last_error'][:100] + "..." if len(site['last_error']) > 100 else site['last_error']
                print(f"      ❌ Error: {error}")
            print()
            
    except Exception as e:
        print(f"❌ Gabim: {e}")

if __name__ == "__main__":
    check_websites() 