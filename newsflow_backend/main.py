"""
Main entry point for the NewsFlow AI Editor backend API.

This module defines a FastAPI application that exposes endpoints for
managing articles scraped from the web, processing them with a language
model, coordinating collaborative review via Telegram and publishing
to WordPress.  The implementation here is intentionally minimal:
it provides the scaffolding for a fully fledged SaaS while keeping
the core logic clear and easy to extend. Production deployments would
add authentication, robust error handling and asynchronous task queues.
"""

from typing import List

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import SessionLocal, engine
from .scraper import scrape_articles
from .llm import process_article
from .telegram_bot import send_article_for_review, telegram_bot
from .wordpress import publish_to_wordpress
from .schemas import ScrapeRequest
from .scheduler import scheduler, get_websites, create_website, update_website, delete_website, Website

# Create database tables on startup. In a real application you would
# manage migrations separately (e.g. with Alembic) but this suffices
# for a development skeleton.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="NewsFlow AI Editor", version="1.0.0")

@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "NewsFlow AI Editor API is running", "status": "ok"}


def get_db():
    """Provide a database session to path operations.

    This dependency yields a SQLAlchemy SessionLocal instance and
    ensures that it is properly closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/scrape", response_model=List[schemas.Article])
def trigger_scrape(
    background_tasks: BackgroundTasks,
    request: schemas.ScrapeRequest = Body(...),
    db: Session = Depends(get_db)
):
    """Fetch new articles with media and queue them for processing nga një URL të dhënë duke përdorur metodën e zgjedhur."""
    scraped = scrape_articles(request.url, request.method.value)
    created_articles: List[models.Article] = []
    for data in scraped:
        # Create article with media data
        article_data = {
            "title": data["title"],
            "url": data["url"], 
            "content": data["content"],
            "images": data.get("images", []),
            "videos": data.get("videos", [])
        }
        article = crud.create_article(db, article_data)
        # Process with LLM only on first import
        if not article.content_processed:
            processed = process_article(article)
            article.content_processed = processed
        db.commit()
        db.refresh(article)
        created_articles.append(article)
        # Schedule Telegram notification
        background_tasks.add_task(send_article_for_review, article)
    return created_articles


@app.get("/articles", response_model=List[schemas.Article])
def list_articles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a paginated list of articles."""
    return crud.get_articles(db, skip=skip, limit=limit)


@app.get("/articles/{article_id}", response_model=schemas.Article)
def read_article(article_id: int, db: Session = Depends(get_db)):
    """Return a single article by identifier."""
    article = crud.get_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@app.post("/articles/{article_id}/approve")
def approve_article(article_id: int, db: Session = Depends(get_db)):
    """Mark an article as approved and publish it to WordPress."""
    article = crud.get_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    # Publish via WordPress integration. The stub returns a dummy ID.
    wp_id = publish_to_wordpress(article)
    article.status = "published"
    article.wordpress_id = wp_id
    db.commit()
    return {"message": "Article published", "wordpress_id": wp_id}


@app.post("/articles/{article_id}/reject")
def reject_article(article_id: int, db: Session = Depends(get_db)):
    """Reject an article so it will not be published."""
    article = crud.get_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = "rejected"
    db.commit()
    return {"message": "Article rejected"}


@app.post("/articles/{article_id}/edit", response_model=schemas.Article)
def edit_article(article_id: int, instruction: schemas.EditInstruction, db: Session = Depends(get_db)):
    """Apply an edit instruction to an article's processed content."""
    article = crud.get_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    # Apply user-provided instructions using the LLM stub
    edited_content = process_article(article, instruction.text)
    article.content_processed = edited_content
    article.status = "edited"
    db.commit()
    db.refresh(article)
    return article


@app.post("/articles/{article_id}/process")
def process_existing_article(article_id: int, db: Session = Depends(get_db)):
    """Process an existing article with LLM professional standards."""
    article = crud.get_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        # Process with LLM using professional journalism standards
        processed_content = process_article(article)
        article.content_processed = processed_content
        article.status = "scraped"  # Keep as scraped, ready for review
        db.commit()
        db.refresh(article)
        return {
            "message": "Article processed successfully with LLM",
            "article_id": article_id,
            "title": article.title,
            "status": article.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing article: {str(e)}")


@app.post("/articles/{article_id}/send_for_review")
def send_existing_article_for_review(article_id: int, db: Session = Depends(get_db)):
    """Send an existing article to Telegram for review."""
    article = crud.get_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        # Send to Telegram for review
        send_article_for_review(article)
        return {
            "message": "Article sent to Telegram for review",
            "article_id": article_id,
            "title": article.title,
            "status": "sent_for_review"
        }
    except Exception as e:
        # Don't fail hard if Telegram fails, just log it
        return {
            "message": "Article processed but Telegram send failed",
            "article_id": article_id,
            "title": article.title,
            "telegram_error": str(e),
            "status": "telegram_error"
        }


@app.post("/telegram/start")
async def start_telegram_bot():
    """Start the Telegram bot."""
    try:
        success = await telegram_bot.initialize()
        if success:
            return {"message": "Telegram bot started successfully", "status": "running"}
        else:
            return {"message": "Failed to start Telegram bot", "status": "error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting bot: {str(e)}")

# Scheduler Management Endpoints
@app.post("/scheduler/start")
async def start_scheduler():
    """Start the automatic news scraping scheduler."""
    try:
        await scheduler.start()
        return {"message": "Scheduler started successfully", "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")

@app.post("/scheduler/stop") 
async def stop_scheduler():
    """Stop the automatic news scraping scheduler."""
    try:
        await scheduler.stop()
        return {"message": "Scheduler stopped successfully", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")

@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status."""
    return {
        "running": scheduler.running,
        "active_tasks": len([t for t in scheduler.tasks.values() if not t.done()]),
        "total_tasks": len(scheduler.tasks)
    }

# Website Management Endpoints
@app.get("/websites")
def list_websites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all websites being monitored."""
    websites = get_websites(db, skip=skip, limit=limit)
    return websites

@app.post("/websites")
def add_website(website_data: dict, db: Session = Depends(get_db)):
    """Add a new website for monitoring."""
    try:
        # Validate required fields
        if not website_data.get("name") or not website_data.get("url"):
            raise HTTPException(status_code=400, detail="Name and URL are required")
        
        # Set defaults
        website_data.setdefault("active", True)
        website_data.setdefault("scrape_interval_minutes", 5)
        
        website = create_website(db, website_data)
        return {
            "message": f"Website '{website.name}' added successfully",
            "website": website
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding website: {str(e)}")

@app.put("/websites/{website_id}")
def update_website_config(website_id: int, website_data: dict, db: Session = Depends(get_db)):
    """Update website configuration."""
    try:
        website = update_website(db, website_id, website_data)
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        return {
            "message": f"Website '{website.name}' updated successfully",
            "website": website
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating website: {str(e)}")

@app.delete("/websites/{website_id}")
def remove_website(website_id: int, db: Session = Depends(get_db)):
    """Remove a website from monitoring."""
    try:
        success = delete_website(db, website_id)
        if not success:
            raise HTTPException(status_code=404, detail="Website not found")
        
        return {"message": "Website removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing website: {str(e)}")

@app.post("/websites/{website_id}/toggle")
def toggle_website(website_id: int, db: Session = Depends(get_db)):
    """Toggle website active status."""
    try:
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        website.active = not website.active
        db.commit()
        
        status = "activated" if website.active else "deactivated"
        return {
            "message": f"Website '{website.name}' {status}",
            "website": website
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling website: {str(e)}")


@app.get("/telegram/status")
def get_telegram_bot_status():
    """Get the status of the Telegram bot."""
    is_initialized = telegram_bot.application is not None
    cache_size = len(telegram_bot.article_cache)
    
    return {
        "bot_initialized": is_initialized,
        "articles_in_cache": cache_size,
        "status": "running" if is_initialized else "stopped"
    }

@app.get("/scraping/methods")
def get_scraping_methods():
    """Get available scraping methods with descriptions."""
    methods = [
        {
            "value": "requests",
            "label": "Requests (Standard)",
            "description": "Metodë e shpejtë me BeautifulSoup",
            "recommended": True
        },
        {
            "value": "requests_advanced", 
            "label": "Requests (Advanced)",
            "description": "Për faqe komplekse me anti-bot protection",
            "recommended": False
        },
        {
            "value": "scrapy",
            "label": "Scrapy Framework",
            "description": "Framework i fuqishëm me CSS selectors",
            "recommended": False
        },
        {
            "value": "intelligent",
            "label": "Scrapy Intelligent ⭐",
            "description": "Engine i inteligjentë që gjen vetëm lajmet e reja",
            "recommended": True,
            "new": True
        }
    ]
    
    # Kontrollo nëse Scrapy është i disponueshëm
    try:
        from .scrapy_engine import scrapy_engine
        scrapy_available = True
    except ImportError:
        scrapy_available = False
        # Hiq Scrapy nga lista nëse nuk është i disponueshëm
        methods = [m for m in methods if m["value"] != "scrapy"]
    
    # Kontrollo nëse Intelligent është i disponueshëm
    try:
        from .scrapy_intelligent import scrape_with_intelligent_scrapy
        intelligent_available = True
    except ImportError:
        intelligent_available = False
        # Hiq Intelligent nga lista nëse nuk është i disponueshëm
        methods = [m for m in methods if m["value"] != "intelligent"]
    
    default_method = "intelligent" if intelligent_available else "requests"
    
    return {
        "methods": methods,
        "default": default_method,
        "scrapy_available": scrapy_available,
        "intelligent_available": intelligent_available
    }