"""
Automatic news scraping scheduler for NewsFlow AI Editor.

This module manages continuous scraping of multiple websites at configurable intervals.
It monitors websites for new articles and automatically processes them through the pipeline.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON

from . import models, crud
from .database import SessionLocal, engine
from .scraper import scrape_articles
from .llm import process_article
from .telegram_bot import send_article_for_review

# Setup logging
logger = logging.getLogger(__name__)

class Website(models.Base):
    """Website model for scheduled scraping."""
    __tablename__ = "websites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Display name
    url = Column(String, nullable=False, unique=True)
    active = Column(Boolean, default=True)
    scrape_interval_minutes = Column(Integer, default=5)  # How often to scrape
    last_scraped = Column(DateTime, nullable=True)
    last_article_title = Column(String, nullable=True)  # Track latest article to avoid duplicates
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Statistics
    total_articles_scraped = Column(Integer, default=0)
    last_error = Column(String, nullable=True)
    error_count = Column(Integer, default=0)

# Create the websites table
models.Base.metadata.create_all(bind=engine)

class NewsFlowScheduler:
    """Manages automatic scraping of multiple websites."""
    
    def __init__(self):
        self.running = False
        self.tasks = {}  # Store running tasks for each website
        
    async def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        logger.info("🚀 NewsFlow Scheduler started")
        
        # Start monitoring task
        asyncio.create_task(self._monitor_websites())
        
    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        
        # Cancel all running tasks
        for task in self.tasks.values():
            if not task.done():
                task.cancel()
        
        self.tasks.clear()
        logger.info("⏹️ NewsFlow Scheduler stopped")
        
    async def _monitor_websites(self):
        """Main monitoring loop."""
        while self.running:
            try:
                db = SessionLocal()
                try:
                    # Get all active websites
                    websites = db.query(Website).filter(Website.active == True).all()
                    
                    for website in websites:
                        # Check if it's time to scrape this website
                        if self._should_scrape_website(website):
                            # Start scraping task if not already running
                            if website.id not in self.tasks or self.tasks[website.id].done():
                                self.tasks[website.id] = asyncio.create_task(
                                    self._scrape_website(website.id)
                                )
                                
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                
            # Check every 30 seconds
            await asyncio.sleep(30)
            
    def _should_scrape_website(self, website: Website) -> bool:
        """Check if a website should be scraped now."""
        if not website.last_scraped:
            return True
            
        time_since_last = datetime.utcnow() - website.last_scraped
        interval = timedelta(minutes=website.scrape_interval_minutes)
        
        return time_since_last >= interval
        
    async def _scrape_website(self, website_id: int):
        """Scrape a specific website."""
        db = SessionLocal()
        try:
            website = db.query(Website).filter(Website.id == website_id).first()
            if not website:
                return
                
            logger.info(f"📡 Scraping {website.name} ({website.url})")
            
            try:
                # Scrape the website using Scrapy Intelligent (default method)
                articles = scrape_articles(website.url, method="intelligent")
                
                if not articles:
                    logger.info(f"📰 No new articles found at {website.name}")
                    website.last_scraped = datetime.utcnow()
                    db.commit()
                    return
                
                # Process the latest article
                latest_article = articles[0]
                
                # Check if this is a new article (avoid duplicates)
                if website.last_article_title and website.last_article_title == latest_article.get('title'):
                    logger.info(f"📰 No new articles at {website.name} (same title as last)")
                    website.last_scraped = datetime.utcnow()
                    db.commit()
                    return
                
                # Create article in database
                article_data = {
                    "title": latest_article.get("title", "Lajm i ri"),
                    "url": latest_article.get("url", website.url),
                    "content": latest_article.get("content", ""),
                    "images": latest_article.get("images", []),
                    "videos": latest_article.get("videos", [])
                }
                
                article = crud.create_article(db, article_data)
                
                # Process with LLM
                if latest_article.get("content"):
                    try:
                        processed_content = process_article(latest_article["content"])
                        if processed_content:
                            article.content_processed = processed_content
                            db.commit()
                    except Exception as e:
                        logger.error(f"LLM processing failed: {e}")
                        article.content_processed = latest_article["content"]
                        db.commit()
                
                # Send to Telegram for review
                try:
                    send_article_for_review(article)
                    logger.info(f"✅ Article from {website.name} sent to Telegram for review")
                except Exception as e:
                    logger.error(f"Failed to send to Telegram: {e}")
                
                # Update website stats
                website.last_scraped = datetime.utcnow()
                website.last_article_title = latest_article.get("title")
                website.total_articles_scraped += 1
                website.error_count = 0  # Reset error count on success
                website.last_error = None
                
                logger.info(f"🎉 Successfully processed article from {website.name}: {latest_article.get('title', 'Untitled')}")
                
            except Exception as e:
                # Update error info
                website.last_scraped = datetime.utcnow()
                website.error_count += 1
                website.last_error = str(e)[:500]  # Limit error message length
                logger.error(f"❌ Error scraping {website.name}: {e}")
                
            db.commit()
            
        except Exception as e:
            logger.error(f"Database error for website {website_id}: {e}")
        finally:
            db.close()

# Global scheduler instance
scheduler = NewsFlowScheduler()

def get_websites(db: Session, skip: int = 0, limit: int = 100):
    """Get all websites."""
    return db.query(Website).offset(skip).limit(limit).all()

def create_website(db: Session, website_data: Dict[str, Any]):
    """Create a new website for monitoring."""
    website = Website(**website_data)
    db.add(website)
    db.commit()
    db.refresh(website)
    return website

def update_website(db: Session, website_id: int, website_data: Dict[str, Any]):
    """Update a website."""
    website = db.query(Website).filter(Website.id == website_id).first()
    if website:
        for key, value in website_data.items():
            setattr(website, key, value)
        db.commit()
        db.refresh(website)
    return website

def delete_website(db: Session, website_id: int):
    """Delete a website."""
    website = db.query(Website).filter(Website.id == website_id).first()
    if website:
        db.delete(website)
        db.commit()
        return True
    return False 