#!/usr/bin/env python3
"""
Script për të startuar NewsFlow Telegram Bot.

Përdorimi:
    python run_telegram_bot.py

Ose me variablat e mjedisit:
    TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHANNEL_ID=your_channel python run_telegram_bot.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from newsflow_backend.telegram_bot import telegram_bot

async def main():
    """Main function to start the Telegram bot."""
    print("🤖 Starting NewsFlow Telegram Bot...")
    
    # Initialize the bot
    if await telegram_bot.initialize():
        print("✅ Bot initialized successfully!")
        print(f"📋 Channel ID: {os.getenv('TELEGRAM_CHANNEL_ID', 'Not set')}")
        print(f"👤 Admin ID: {os.getenv('TELEGRAM_ADMIN_USER_ID', 'Not set')}")
        print("\n🚀 Starting polling... (Press Ctrl+C to stop)")
        
        # Start polling
        await telegram_bot.start_polling()
    else:
        print("❌ Failed to initialize bot!")
        print("\n📝 To configure the bot:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Get your bot token")
        print("3. Set environment variables:")
        print("   - TELEGRAM_BOT_TOKEN=your_bot_token")
        print("   - TELEGRAM_CHANNEL_ID=your_channel_id")
        print("   - TELEGRAM_ADMIN_USER_ID=your_user_id")
        print("\nOr create a .env file with these variables.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}") 