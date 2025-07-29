#!/usr/bin/env python3

import requests
import json

def add_new_websites():
    """Shton website-et e reja në sistem"""
    
    new_websites = [
        {
            "name": "Shkodra Zone",
            "url": "https://shkodrazone.com/",
            "active": True
        },
        {
            "name": "Realiteti Post",
            "url": "https://realitetipost.net/",
            "active": True
        }
    ]
    
    print("🌐 SHTIMI I WEBSITE-EVE TË REJA")
    print("=" * 50)
    
    for website in new_websites:
        try:
            print(f"📝 Duke shtuar: {website['name']} ({website['url']})")
            
            response = requests.post(
                "http://localhost:8000/websites",
                json=website,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ U shtua me sukses! ID: {result.get('id')}")
            else:
                print(f"❌ Gabim: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 30)
    
    # Kontrollo të gjitha website-et
    print("\n📊 LISTA E TË GJITHA WEBSITE-EVE:")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/websites", timeout=10)
        if response.status_code == 200:
            websites = response.json()
            
            for website in websites:
                status = "✅ AKTIV" if website.get('active') else "❌ JOAKTIV"
                method = website.get('scraping_method', 'unknown')
                print(f"📰 {website['name']} - {status} - {method}")
                print(f"   🔗 {website['url']}")
                print()
        else:
            print(f"❌ Gabim në marrjen e listës: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_new_websites() 