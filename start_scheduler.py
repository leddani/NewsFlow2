#!/usr/bin/env python3
"""
Script për të startuar NewsFlow scheduler-in
"""
import requests

def start_scheduler():
    try:
        print("🔄 Duke startuar scheduler...")
        response = requests.post('http://localhost:8000/scheduler/start')
        print(f"📡 Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Scheduler startua me sukses!")
        else:
            print("❌ Gabim në startimin e scheduler-it!")
            
    except Exception as e:
        print(f"❌ Gabim: {e}")

if __name__ == "__main__":
    start_scheduler() 