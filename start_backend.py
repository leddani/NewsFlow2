#!/usr/bin/env python3
"""
Skript për të nisur NewsFlow AI Editor backend-in
"""
import uvicorn
import signal
import sys

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    print("\n🛑 Duke ndalur NewsFlow AI Editor...")
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Duke startuar NewsFlow AI Editor backend...")
    print("📍 Port: 8000")
    print("🌐 Host: 0.0.0.0") 
    print("🔗 URL: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("-" * 50)
    
    try:
        # Run uvicorn in the main thread (blocking call)
        uvicorn.run(
            "newsflow_backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server ndaluar nga përdoruesi.")
    except Exception as e:
        print(f"\n❌ Gabim në server: {e}")
    finally:
        print("👋 NewsFlow AI Editor backend u mbyll.") 