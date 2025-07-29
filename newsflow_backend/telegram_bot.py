"""
Telegram integration for NewsFlow AI Editor.

This module provides a complete Telegram bot implementation for
sending scraped and processed articles to a Telegram channel or group
for review, with inline buttons for approve, reject and edit actions.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
import logging

# =======================
# K R E D E N C I A L E T
# =======================
# (Opsionale) Lexo .env nëse ekziston
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Token nga BotFather (fallback = ai në foto). Rekomandohet ta vendosësh si ENV.
TELEGRAM_BOT_TOKEN: str = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "8292510775:AAH4vxI8DdLUcwW4qLpkaoz7FRetwkBU5og"
).strip()

# TARGET mund të jetë:
# - ID numerik user/grup/kanal (p.sh. -100xxxxxxxxxx ose 1379911001)
# - ose @username i kanalit (p.sh. @newsflowchannel)
# DM me LedD → 1379911001; për kanal → @EmriKanalit ose -100…
TELEGRAM_TARGET: str = os.getenv("TELEGRAM_TARGET", "1379911001").strip()

# Admin user id (për kontrolle)
TELEGRAM_ADMIN_USER_ID: int = int(os.getenv("TELEGRAM_ADMIN_USER_ID", "1379911001"))

# Do të vendoset në runtime nga _resolve_target()
TELEGRAM_CHANNEL_ID: int | None = None

async def _resolve_target(application: Application) -> None:
    """
    Normalizon TELEGRAM_TARGET -> TELEGRAM_CHANNEL_ID (int).
    - Nëse është @username (kanal), përdor get_chat për të marrë -100…
    - Nëse është numerik, ktheje në int.
    """
    global TELEGRAM_CHANNEL_ID
    target = (TELEGRAM_TARGET or "").strip()

    if not TELEGRAM_BOT_TOKEN or ":" not in TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN mungon ose është i pavlefshëm.")

    if target.startswith("@"):
        chat = await application.bot.get_chat(target)  # boti duhet të jetë admin në kanal
        TELEGRAM_CHANNEL_ID = int(chat.id)
    else:
        TELEGRAM_CHANNEL_ID = int(target)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class NewsFlowTelegramBot:
    def __init__(self):
        self.application: Optional[Application] = None
        self.article_cache: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize the Telegram bot application."""
        if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            logger.warning("Telegram bot token not configured. Bot will not start.")
            return False
            
        try:
            self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))

            # >>> R R E G U L L I M I   K R Y E S O R   I   K R E D E N C I A L E V E <<<
            await _resolve_target(self.application)

            # Initialize the bot (needed for webhook mode)
            await self.application.initialize()
            await self.application.start()
            
            # Start polling in background task
            import asyncio
            asyncio.create_task(self._start_polling())
            
            logger.info("Telegram bot initialized and started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            return False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🤖 *Mirë se vini në NewsFlow AI Editor Bot!*\n\n"
            "Ky bot ju ndihmon të menaxhoni artikujt e lajmeve:\n\n"
            "📰 *Komandat e disponueshme:*\n"
            "/start - Shfaq këtë mesazh\n"
            "/help - Ndihmë për komandat\n"
            "/status - Statusi i bot-it\n\n"
            "Artikujt e skrapuar do të dërgohen këtu për review."
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            "📖 *Ndihmë për NewsFlow Bot*\n\n"
            "🔹 *Komandat:*\n"
            "• /start - Fillo bot-in\n"
            "• /help - Shfaq këtë ndihmë\n"
            "• /status - Kontrollo statusin\n\n"
            "🔹 *Butonat për artikujt:*\n"
            "• ✅ Aprovo - Aprovo artikullin\n"
            "• ❌ Refuzo - Refuzo artikullin\n"
            "• ✏️ Edito - Kërko redaktim\n"
            "• 📝 Detaje - Shfaq më shumë informacion\n\n"
            "🔹 *Statusi i artikujve:*\n"
            "• 🟡 Në pritje - Duke pritur review\n"
            "• 🟢 Aprovuar - Gati për publikim\n"
            "• 🔴 Refuzuar - Nuk do të publikohet"
        )
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        status_message = (
            "📊 *Statusi i NewsFlow Bot*\n\n"
            f"🤖 Bot: {'🟢 Aktiv' if self.application else '🔴 Jo aktiv'}\n"
            f"📰 Artikuj në cache: {len(self.article_cache)}\n"
            f"📋 Channel ID: {TELEGRAM_CHANNEL_ID}\n"
            f"👤 Admin ID: {TELEGRAM_ADMIN_USER_ID}"
        )
        
        await update.message.reply_text(
            status_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Button callback received: {data}")
        
        # Extract article_id properly based on callback data format
        article_id = None
        
        # Different formats: approve_article_123, manual_edit_article_123, etc.
        if data.startswith("approve_") or data.startswith("reject_") or data.startswith("edit_") or data.startswith("details_"):
            # Standard format: action_article_123
            parts = data.split('_', 1)
            if len(parts) > 1:
                article_id = parts[1]
        elif data.startswith("manual_edit_") or data.startswith("llm_edit_"):
            # Edit format: manual_edit_article_123 or llm_edit_article_123
            parts = data.split('_', 2)  # Split into 3 parts: ['manual', 'edit', 'article_123']
            if len(parts) > 2:
                article_id = parts[2]
        elif data.startswith("llm_"):
            # LLM edit types: llm_improve_sq_article_123, llm_custom_article_123, etc.
            parts = data.split('_')
            # Find the part that starts with 'article_'
            for i, part in enumerate(parts):
                if part == 'article' and i + 1 < len(parts):
                    article_id = f"article_{parts[i + 1]}"
                    break
        elif data.startswith("back_") or data.startswith("reject_edit_"):
            # Back/reject edit format: back_article_123
            parts = data.split('_', 1)
            if len(parts) > 1:
                article_id = parts[1]
        
        logger.info(f"Parsed article_id: {article_id}, available articles: {list(self.article_cache.keys())}")
        
        if not article_id or article_id not in self.article_cache:
            await query.edit_message_text(
                f"❌ Artikulli nuk u gjet!\n"
                f"🔍 ID kërkuar: {article_id}\n"
                f"📋 Të disponueshëm: {list(self.article_cache.keys())}"
            )
            return
        
        article = self.article_cache[article_id]
        
        # Route to appropriate handlers
        if data.startswith("approve_"):
            await self.approve_article(query, article_id, article)
        elif data.startswith("reject_"):
            await self.reject_article(query, article_id, article)
        elif data.startswith("edit_"):
            await self.request_edit(query, article_id, article)
        elif data.startswith("details_"):
            await self.show_details(query, article_id, article)
        elif data.startswith("manual_edit_"):
            await self.handle_manual_edit(query, article_id, article)
        elif data.startswith("llm_edit_"):
            await self.handle_llm_edit(query, article_id, article)
        elif data.startswith("llm_improve_sq_"):
            processed_content = await self.process_llm_edit(article_id, article, 'improve_sq')
            if processed_content:
                await self.send_edited_article_for_review(article_id, article, query.message.chat_id)
            else:
                await query.edit_message_text("❌ Redaktimi me LLM dështoi. Provoni përsëri.")
        elif data.startswith("llm_news_style_"):
            processed_content = await self.process_llm_edit(article_id, article, 'news_style')
            if processed_content:
                await self.send_edited_article_for_review(article_id, article, query.message.chat_id)
            else:
                await query.edit_message_text("❌ Redaktimi me LLM dështoi. Provoni përsëri.")
        elif data.startswith("llm_shorten_"):
            processed_content = await self.process_llm_edit(article_id, article, 'shorten')
            if processed_content:
                await self.send_edited_article_for_review(article_id, article, query.message.chat_id)
            else:
                await query.edit_message_text("❌ Redaktimi me LLM dështoi. Provoni përsëri.")
        elif data.startswith("llm_expand_"):
            processed_content = await self.process_llm_edit(article_id, article, 'expand')
            if processed_content:
                await self.send_edited_article_for_review(article_id, article, query.message.chat_id)
            else:
                await query.edit_message_text("❌ Redaktimi me LLM dështoi. Provoni përsëri.")
        elif data.startswith("llm_custom_"):
            await self.handle_llm_custom_edit(query, article_id, article)
        elif data.startswith("back_"):
            await self.request_edit(query, article_id, article)
        elif data.startswith("reject_edit_"):
            await self.reject_article(query, article_id, article)
    
    async def approve_article(self, query, article_id: str, article: Dict[str, Any]):
        """Approve an article and publish to WordPress."""
        article['status'] = 'approved'
        article['reviewer'] = query.from_user.username or query.from_user.first_name
        
        # Initial approval message
        initial_message = (
            f"✅ *Artikulli u aprovua!*\n\n"
            f"📰 **{article['title']}**\n"
            f"🔗 {article['url']}\n"
            f"👤 Aprova: {article['reviewer']}\n"
            f"⏰ {article.get('reviewed_at', 'Tani')}\n\n"
            f"📤 *Po publikohet në WordPress...*"
        )
        
        await query.edit_message_text(
            initial_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Publish to WordPress
        wordpress_url = None
        try:
            # Import here to avoid circular imports
            from .wordpress import publish_to_wordpress
            from .models import Article
            
            # Create a mock article object for WordPress publishing
            class MockArticle:
                def __init__(self, article_data):
                    self.id = article_data.get('id')
                    self.title = article_data.get('title')
                    self.content = article_data.get('content')
                    self.content_processed = article_data.get('content_processed')
                    self.images = article_data.get('images', [])
                    self.videos = article_data.get('videos', [])
            
            mock_article = MockArticle(article)
            logger.info(f"🚀 Publishing article {article_id} to WordPress...")
            
            wordpress_url = publish_to_wordpress(mock_article)
            
            if wordpress_url:
                # Success message with WordPress URL
                success_message = (
                    f"✅ *Artikulli u publikua me sukses!*\n\n"
                    f"📰 **{article['title']}**\n"
                    f"🔗 Burimi: {article['url']}\n"
                    f"👤 Aprova: {article['reviewer']}\n"
                    f"📝 WordPress: {wordpress_url}\n"
                    f"📸 Imazhe: {len(article.get('images', []))}\n"
                    f"🎥 Video: {len(article.get('videos', []))}\n"
                    f"⏰ Publikuar: Tani"
                )
                article['wordpress_url'] = wordpress_url
                article['wordpress_status'] = 'published'
                logger.info(f"✅ Article {article_id} successfully published to WordPress: {wordpress_url}")
            else:
                # Error message
                success_message = (
                    f"✅ *Artikulli u aprovua!*\n"
                    f"⚠️ *Por publikimi në WordPress dështoi*\n\n"
                    f"📰 **{article['title']}**\n"
                    f"🔗 {article['url']}\n"
                    f"👤 Aprova: {article['reviewer']}\n"
                    f"❌ WordPress: Gabim në publikim\n"
                    f"⏰ {article.get('reviewed_at', 'Tani')}\n\n"
                    f"💡 *Kontrollo konfigurimin e WordPress*"
                )
                article['wordpress_status'] = 'failed'
                logger.error(f"❌ WordPress publishing failed for article {article_id}")
                
        except Exception as e:
            logger.error(f"❌ Error publishing to WordPress: {e}")
            # Error message
            success_message = (
                f"✅ *Artikulli u aprovua!*\n"
                f"❌ *Gabim në publikimin në WordPress*\n\n"
                f"📰 **{article['title']}**\n"
                f"🔗 {article['url']}\n"
                f"👤 Aprova: {article['reviewer']}\n"
                f"⚠️ Gabim: {str(e)[:100]}...\n"
                f"⏰ {article.get('reviewed_at', 'Tani')}"
            )
            article['wordpress_status'] = 'error'
        
        # Update the message with final status
        await query.edit_message_text(
            success_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Article {article_id} approved by {article['reviewer']}")
    
    async def reject_article(self, query, article_id: str, article: Dict[str, Any]):
        """Reject an article."""
        article['status'] = 'rejected'
        article['reviewer'] = query.from_user.username or query.from_user.first_name
        
        message = (
            f"❌ *Artikulli u refuzua!*\n\n"
            f"📰 **{article['title']}**\n"
            f"🔗 {article['url']}\n"
            f"👤 Refuzoi: {article['reviewer']}\n"
            f"⏰ {article.get('reviewed_at', 'Tani')}"
        )
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # TODO: Update database status
        logger.info(f"Article {article_id} rejected by {article['reviewer']}")
    
    async def request_edit(self, query, article_id: str, article: Dict[str, Any]):
        """Request edit for an article - shows editing options."""
        article['status'] = 'editing'
        article['reviewer'] = query.from_user.username or query.from_user.first_name
        
        # Create editing keyboard
        keyboard = [
            [
                InlineKeyboardButton("📝 Redakto manual", callback_data=f"manual_edit_{article_id}"),
                InlineKeyboardButton("🤖 Redakto me LLM", callback_data=f"llm_edit_{article_id}")
            ],
            [
                InlineKeyboardButton("🔙 Kthehu", callback_data=f"back_{article_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show current content for editing
        content_preview = article['content_processed'][:800] + "..." if len(article['content_processed']) > 800 else article['content_processed']
        
        message = (
            f"✏️ *REDAKTIMI I ARTIKULLIT*\n\n"
            f"📰 **{article['title']}**\n\n"
            f"📝 *Përmbajtja aktuale:*\n{content_preview}\n\n"
            f"👆 *Zgjidhni mënyrën e redaktimit:*"
        )
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        logger.info(f"Article {article_id} entering edit mode - requested by {article['reviewer']}")

    async def handle_manual_edit(self, query, article_id: str, article: Dict[str, Any]):
        """Handle manual text editing."""
        # Send the current content as a message that user can copy/edit
        content = article['content_processed']
        
        # Split content if too long for single message
        if len(content) > 4000:
            # Send in chunks
            chunk_size = 4000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            
            await query.edit_message_text(
                f"✏️ *REDAKTIM MANUAL*\n\n"
                f"📰 **{article['title']}**\n\n"
                f"📝 Përmbajtja është shumë e gjatë. Po dërgoj në pjesë...\n"
                f"Kopjo, redakto dhe dërgo tekstin e ri si përgjigje.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            for i, chunk in enumerate(chunks, 1):
                await self.application.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"📄 *Pjesa {i}/{len(chunks)}:*\n\n{chunk}",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await query.edit_message_text(
                f"✏️ *REDAKTIM MANUAL*\n\n"
                f"📰 **{article['title']}**\n\n"
                f"📝 *Përmbajtja për redaktim:*\n\n{content}\n\n"
                f"👆 Kopjo tekstin, redaktoje dhe dërgoja si përgjigje për ta ruajtur.\n"
                f"Ose përdor /cancel për të anulluar.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Set user state for expecting edited text
        if not hasattr(self, 'user_states'):
            self.user_states = {}
        self.user_states[query.from_user.id] = {
            'action': 'manual_edit',
            'article_id': article_id,
            'article': article
        }
        
        logger.info(f"Manual edit started for article {article_id}")

    async def handle_llm_edit(self, query, article_id: str, article: Dict[str, Any]):
        """Handle LLM-assisted editing."""
        keyboard = [
            [
                InlineKeyboardButton("🇦🇱 Përmirëso në shqip", callback_data=f"llm_improve_sq_{article_id}"),
                InlineKeyboardButton("📰 Bëje më gazetaresk", callback_data=f"llm_news_style_{article_id}")
            ],
            [
                InlineKeyboardButton("📝 Shkurto", callback_data=f"llm_shorten_{article_id}"),
                InlineKeyboardButton("📖 Zgjato", callback_data=f"llm_expand_{article_id}")
            ],
            [
                InlineKeyboardButton("🎯 Redaktim i personalizuar", callback_data=f"llm_custom_{article_id}")
            ],
            [
                InlineKeyboardButton("🔙 Kthehu", callback_data=f"edit_{article_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        content_preview = article['content_processed'][:500] + "..." if len(article['content_processed']) > 500 else article['content_processed']
        
        message = (
            f"🤖 *REDAKTIM ME LLM*\n\n"
            f"📰 **{article['title']}**\n\n"
            f"📝 *Përmbajtja aktuale:*\n{content_preview}\n\n"
            f"👆 *Zgjidhni tipin e redaktimit:*"
        )
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def handle_llm_custom_edit(self, query, article_id: str, article: Dict[str, Any]):
        """Handle custom LLM editing with user instructions."""
        await query.edit_message_text(
            f"🎯 *REDAKTIM I PERSONALIZUAR*\n\n"
            f"📰 **{article['title']}**\n\n"
            f"📝 Shkruaj udhëzimet për LLM-në:\n"
            f"Shembull: 'Bëje më të shkurtër dhe më dramatik'\n"
            f"Ose: 'Shto më shumë detaje për ekonominë'\n"
            f"Ose: 'Ndrysho tonin në më pozitiv'\n\n"
            f"💬 Dërgo udhëzimet si përgjigje ose /cancel për të anulluar.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Set user state for expecting custom instructions
        if not hasattr(self, 'user_states'):
            self.user_states = {}
        self.user_states[query.from_user.id] = {
            'action': 'llm_custom_edit',
            'article_id': article_id,
            'article': article
        }

    async def process_llm_edit(self, article_id: str, article: Dict[str, Any], edit_type: str):
        """Process article with LLM based on edit type."""
        from .llm import process_article_with_instructions
        
        # Define prompts for different edit types
        prompts = {
            'improve_sq': 'Përmirëso këtë tekst në shqip duke ruajtur të gjitha informacionet, por bëje më të qartë dhe më professional.',
            'news_style': 'Rishkruaje këtë tekst në stil gazetaresk profesional, duke ruajtur të gjitha faktet.',
            'shorten': 'Shkurto këtë tekst në 60% të gjatësisë origjinale duke ruajtur informacionet kryesore.',
            'expand': 'Zgjero këtë tekst duke shtuar më shumë detaje dhe kontekst, por mos shpik fakte të reja.'
        }
        
        prompt = prompts.get(edit_type, 'Përmirëso këtë tekst.')
        
        try:
            # Process with LLM
            processed_content = await process_article_with_instructions(
                article['content_processed'], 
                prompt
            )
            
            if processed_content:
                # Update article with new content
                article['content_processed'] = processed_content
                article['status'] = 'edited'
                
                return processed_content
            else:
                return None
        except Exception as e:
            logger.error(f"LLM edit failed: {e}")
            return None

    async def send_edited_article_for_review(self, article_id: str, article: Dict[str, Any], chat_id: int):
        """Send edited article back for final review."""
        # Create final review keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprovo redaktimin", callback_data=f"approve_{article_id}"),
                InlineKeyboardButton("❌ Refuzo redaktimin", callback_data=f"reject_edit_{article_id}")
            ],
            [
                InlineKeyboardButton("✏️ Redakto përsëri", callback_data=f"edit_{article_id}"),
                InlineKeyboardButton("📝 Detaje", callback_data=f"details_{article_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show edited content
        edited_content = article['content_processed']
        if len(edited_content) > 4000:
            content_preview = edited_content[:4000] + "..."
        else:
            content_preview = edited_content
        
        from datetime import datetime
        now = datetime.now()
        date_time = now.strftime("%d/%m/%Y %H:%M")
        
        message = (
            f"✅ *ARTIKULL I REDAKTUAR*\n\n"
            f"📰 **{article['title']}**\n\n"
            f"{content_preview}\n\n"
            f"📅 *Redaktuar:* {date_time}\n\n"
            f"👆 *Vendosni për redaktimin:*"
        )
        
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_details(self, query, article_id: str, article: Dict[str, Any]):
        """Show detailed article information."""
        content_preview = article['content'][:200] + "..." if len(article['content']) > 200 else article['content']
        processed_preview = article['content_processed'][:200] + "..." if len(article['content_processed']) > 200 else article['content_processed']
        
        message = (
            f"📋 *Detajet e artikullit*\n\n"
            f"📰 **{article['title']}**\n"
            f"🔗 {article['url']}\n"
            f"📅 {article.get('scraped_at', 'N/A')}\n"
            f"📊 Status: {article.get('status', 'Në pritje')}\n\n"
            f"📝 *Përmbajtja origjinale:*\n{content_preview}\n\n"
            f"🤖 *Përmbajtja e përpunuar:*\n{processed_preview}"
        )
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def send_article_for_review(self, article) -> bool:
        """Send an article to Telegram for collaborative review with images and videos.

        Args:
            article: A model instance containing title, url, processed content, images and videos.

            Returns:
                bool: True if sent successfully, False otherwise.
        """
        if not self.application:
            logger.warning("Telegram bot not initialized")
            return False
        
        try:
            # Get media data from article attributes
            images = getattr(article, 'images', []) or []
            videos = getattr(article, 'videos', []) or []
            
            # Create article cache entry with media
            article_id = f"article_{article.id}"
            self.article_cache[article_id] = {
                'id': article.id,
                'title': article.title,
                'url': article.url,
                'content': article.content,
                'content_processed': article.content_processed,
                'images': images,
                'videos': videos,
                'status': 'pending',
                'scraped_at': 'Tani'
            }
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Aprovo", callback_data=f"approve_{article_id}"),
                    InlineKeyboardButton("❌ Refuzo", callback_data=f"reject_{article_id}")
                ],
                [
                    InlineKeyboardButton("✏️ Edito", callback_data=f"edit_{article_id}"),
                    InlineKeyboardButton("📝 Detaje", callback_data=f"details_{article_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Create message with media info and length limit for Telegram (4096 chars max)
            processed_content = article.content_processed
            
            # Check if content is processed by LLM
            if processed_content and len(processed_content) > 50:
                # Calculate available space for content (leave space for headers/footers)
                from datetime import datetime
                now = datetime.now()
                date_time = now.strftime("%d/%m/%Y %H:%M")
                
                # Add media info to footer
                media_info = ""
                if images:
                    media_info += f"\n📸 *Imazhe:* {len(images)}"
                if videos:
                    media_info += f"\n🎥 *Video:* {len(videos)}"
                
                header = f"📰 *Lajm i ri për review:*\n\n"
                footer = f"\n\n📅 *Scraping:* {date_time}{media_info}\n\n👆 *Zgjidhni një veprim:*"
                available_space = 4000 - len(header) - len(footer)  # Leave some buffer
                
                # Truncate content if too long
                if len(processed_content) > available_space:
                    truncated_content = processed_content[:available_space-10] + "..."
                else:
                    truncated_content = processed_content
                
                message = header + truncated_content + footer
            else:
                # Fallback for unprocessed content
                from datetime import datetime
                now = datetime.now()
                date_time = now.strftime("%d/%m/%Y %H:%M")
                
                # Add media info
                media_info = ""
                if images:
                    media_info += f"\n📸 *Imazhe:* {len(images)}"
                if videos:
                    media_info += f"\n🎥 *Video:* {len(videos)}"
                
                content_preview = article.content[:300] + "..." if len(article.content) > 300 else article.content
                message = (
                    f"📰 *Artikull për review:*\n\n"
                    f"**{article.title}**\n\n"
                    f"{content_preview}\n\n"
                    f"📅 *Scraping:* {date_time}{media_info}\n\n"
                    f"👆 *Zgjidhni një veprim:*"
                )
            
            # Send main message first
            sent_message = await self.application.bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            # Send up to 2 images if available (Telegram limits)
            if images:
                for i, image_url in enumerate(images[:2]):  # Limit to 2 images to avoid spam
                    try:
                        await self.application.bot.send_photo(
                            chat_id=TELEGRAM_CHANNEL_ID,
                            photo=image_url,
                            caption=f"📸 Imazh {i+1}/{min(len(images), 2)}: {article.title[:30]}..." if len(article.title) > 30 else f"📸 Imazh {i+1}/{min(len(images), 2)}: {article.title}",
                            reply_to_message_id=sent_message.message_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send image {i+1}: {e}")
            
            # Send video links if available  
            if videos:
                video_text = "🎥 *Video të lidhura me lajmin:*\n\n"
                for i, video_url in enumerate(videos[:3]):  # Limit to 3 videos
                    video_text += f"{i+1}. {video_url}\n"
                
                try:
                    await self.application.bot.send_message(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        text=video_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=sent_message.message_id,
                        disable_web_page_preview=False  # Allow video previews
                    )
                except Exception as e:
                    logger.warning(f"Failed to send videos: {e}")
            
            logger.info(f"Article {article.id} sent for review to Telegram with {len(images)} images and {len(videos)} videos")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send article to Telegram: {e}")
            return False
    
    async def _start_polling(self):
        """Internal method to start polling in background."""
        try:
            logger.info("Starting Telegram bot polling in background...")
            await self.application.updater.start_polling()
        except Exception as e:
            logger.error(f"Error during bot polling: {e}")
    
    async def start_polling(self):
        """Start the bot polling."""
        if not self.application:
            logger.error("Cannot start polling - bot not initialized")
            return
        
        try:
            logger.info("Starting Telegram bot polling...")
            await self.application.run_polling()
        except Exception as e:
            logger.error(f"Error during bot polling: {e}")

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for editing and custom instructions."""
        if not hasattr(self, 'user_states'):
            self.user_states = {}
        
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check if user has an active editing state
        if user_id in self.user_states:
            state = self.user_states[user_id]
            action = state.get('action')
            article_id = state.get('article_id')
            article = state.get('article')
            
            if action == 'manual_edit':
                # User sent edited text
                await self.process_manual_edit(update, article_id, article, text)
                del self.user_states[user_id]
                
            elif action == 'llm_custom_edit':
                # User sent custom LLM instructions
                await self.process_custom_llm_edit(update, article_id, article, text)
                del self.user_states[user_id]
        else:
            # No active state, send help message
            await update.message.reply_text(
                "👋 Përshëndetje! Për të përdorur redaktimin:\n"
                "1. Klikoni butonin 'Edito' në një artikull\n"
                "2. Zgjidhni 'Redakto manual' ose 'Redakto me LLM'\n"
                "3. Ndiqni udhëzimet\n\n"
                "Përdorni /help për më shumë informacion."
            )

    async def process_manual_edit(self, update: Update, article_id: str, article: Dict[str, Any], edited_text: str):
        """Process manually edited text."""
        try:
            # Update article with edited content
            article['content_processed'] = edited_text
            article['status'] = 'manually_edited'
            article['edited_by'] = update.effective_user.username or update.effective_user.first_name
            
            # Send confirmation and new review
            await update.message.reply_text(
                f"✅ *Redaktimi manual u ruajt!*\n\n"
                f"📰 **{article['title']}**\n\n"
                f"📝 Karaktere: {len(edited_text)}\n"
                f"👤 Redaktoi: {article['edited_by']}\n\n"
                f"📨 Po dërgoj për review final...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Send edited article for final review
            await self.send_edited_article_for_review(article_id, article, update.effective_chat.id)
            
            logger.info(f"Manual edit completed for article {article_id} by {article['edited_by']}")
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Gabim në ruajtjen e redaktimit: {str(e)}\n"
                f"Provoni përsëri ose kontaktoni administratorin."
            )
            logger.error(f"Manual edit error: {e}")

    async def process_custom_llm_edit(self, update: Update, article_id: str, article: Dict[str, Any], instructions: str):
        """Process custom LLM editing with user instructions."""
        try:
            # Send "processing" message
            processing_msg = await update.message.reply_text(
                f"🤖 *Po përpunoj me LLM...*\n\n"
                f"📰 **{article['title']}**\n"
                f"📝 Instruksione: {instructions}\n\n"
                f"⏳ Ju lutem prisni...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Process with LLM
            from .llm import process_article_with_instructions
            edited_content = await process_article_with_instructions(
                article['content_processed'], 
                instructions
            )
            
            if edited_content:
                # Update article
                article['content_processed'] = edited_content
                article['status'] = 'llm_edited'
                article['edited_by'] = update.effective_user.username or update.effective_user.first_name
                article['edit_instructions'] = instructions
                
                # Delete processing message
                await processing_msg.delete()
                
                # Send success message
                await update.message.reply_text(
                    f"✅ *Redaktimi me LLM u krye!*\n\n"
                    f"📰 **{article['title']}**\n"
                    f"📝 Instruksione: {instructions}\n"
                    f"📊 Karaktere: {len(edited_content)}\n"
                    f"👤 Redaktoi: {article['edited_by']}\n\n"
                    f"📨 Po dërgoj për review final...",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Send edited article for final review
                await self.send_edited_article_for_review(article_id, article, update.effective_chat.id)
                
                logger.info(f"Custom LLM edit completed for article {article_id}: {instructions}")
                
            else:
                # LLM processing failed
                await processing_msg.edit_text(
                    f"❌ *Redaktimi me LLM dështoi!*\n\n"
                    f"📰 **{article['title']}**\n"
                    f"📝 Instruksione: {instructions}\n\n"
                    f"🔄 Provoni përsëri me instruksione të ndryshme\n"
                    f"ose zgjidhni redaktim manual.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ Gabim në redaktimin me LLM: {str(e)}\n"
                f"Provoni përsëri ose kontaktoni administratorin."
            )
            logger.error(f"Custom LLM edit error: {e}")

# Global bot instance
telegram_bot = NewsFlowTelegramBot()

def send_article_for_review(article) -> None:
    """Legacy function for backward compatibility."""
    try:
        # Try to get the running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we have a running loop, schedule the coroutine
            import threading
            def run_in_new_thread():
                # Create new event loop in a separate thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(telegram_bot.send_article_for_review(article))
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_new_thread, daemon=True)
            thread.start()
            
        except RuntimeError:
            # No running loop, create a new one
            asyncio.run(telegram_bot.send_article_for_review(article))
            
    except Exception as e:
        # Fallback: just print message like before
        message = (
            f"[Telegram] Review requested for article '{article.title}'.\n"
            f"URL: {article.url}\n"
            f"Content (processed):\n{article.content_processed[:200]}..."
        )
        print(message)
        logger.error(f"Failed to send to Telegram: {e}")
