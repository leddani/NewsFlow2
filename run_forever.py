#!/usr/bin/env python3
"""
Script i thjeshtuar për të mbajtur NewsFlow AI Editor aktiv 24/7.
"""

import subprocess
import time
import sys
import os
import requests
from datetime import datetime

# Konfigurimi
BACKEND_PORT = 8000
CHECK_INTERVAL = 30  # Kontrollo çdo 30 sekonda

class NewsFlowSimple:
    def __init__(self):
        self.backend_process = None
        self.running = True
        
    def log(self, message):
        """Print me timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def check_backend_health(self):
        """Kontrollo nëse backend-i është aktiv."""
        try:
            response = requests.get(f"http://localhost:{BACKEND_PORT}/", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def start_backend(self):
        """Start backend duke përdorur start_backend.py."""
        self.log("🚀 Duke startuar backend...")
        
        # Ndaloj procese ekzistuese
        try:
            subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                          capture_output=True, check=False)
            time.sleep(3)
        except:
            pass
            
        # Start backend-in
        self.backend_process = subprocess.Popen(
            [sys.executable, "start_backend.py"],
            cwd=os.getcwd()
        )
        
        # Prit që backend-i të startojë
        self.log("⏳ Duke pritur që backend-i të startojë...")
        for i in range(20):
            if self.check_backend_health():
                self.log("✅ Backend startua me sukses!")
                return True
            time.sleep(2)
            
        self.log("❌ Backend nuk arriti të startojë!")
        return False
        
    def stop_backend(self):
        """Ndaloj backend-in."""
        if self.backend_process:
            self.log("🛑 Duke ndalur backend...")
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            except:
                try:
                    self.backend_process.kill()
                except:
                    pass
            self.backend_process = None
            
    def start_services(self):
        """Start scheduler dhe telegram bot."""
        time.sleep(5)  # Jep kohë backend-it të stabilizohet
        
        try:
            self.log("📅 Duke startuar scheduler...")
            response = requests.post(f"http://localhost:{BACKEND_PORT}/scheduler/start", timeout=10)
            if response.status_code == 200:
                self.log("✅ Scheduler aktiv!")
            else:
                self.log("⚠️ Scheduler problem")
        except Exception as e:
            self.log(f"⚠️ Scheduler gabim: {e}")
            
        try:
            self.log("📱 Duke startuar Telegram bot...")
            response = requests.post(f"http://localhost:{BACKEND_PORT}/telegram/start", timeout=15)
            if response.status_code == 200:
                self.log("✅ Telegram bot aktiv!")
            else:
                self.log("⚠️ Telegram bot problem")
        except Exception as e:
            self.log(f"⚠️ Telegram bot gabim: {e}")
        
    def run(self):
        """Nis platformën permanent."""
        self.log("🚀 NEWSFLOW AI EDITOR - PERMANENT MODE")
        self.log("=" * 60)
        self.log("📡 10 Website në monitoring")
        self.log("🤖 LLM Processing aktiv") 
        self.log("📱 Telegram Bot në pritje")
        self.log("🔄 Scheduler i vazhdueshëm")
        self.log("=" * 60)
        
        # Start backend-in
        if not self.start_backend():
            self.log("❌ Nuk mund të startoj backend! Duke dalë...")
            return
            
        # Start shërbimet
        self.start_services()
        
        self.log("🎯 PLATFORMA AKTIVE - PO MONITOROJ 24/7")
        self.log("💡 Përdor Ctrl+C për të ndalur")
        
        # Loop monitorimi
        try:
            while self.running:
                if not self.check_backend_health():
                    self.log("❌ Backend nuk përgjigjet! Duke ristartur...")
                    self.start_backend()
                    self.start_services()
                else:
                    self.log("✅ Sistema aktive...")
                    
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            self.log("⌨️ Ctrl+C i detektuar...")
        except Exception as e:
            self.log(f"❌ Gabim: {e}")
        finally:
            self.stop_backend()
            self.log("👋 NewsFlow AI Editor u ndal.")

if __name__ == "__main__":
    daemon = NewsFlowSimple()
    daemon.run() 