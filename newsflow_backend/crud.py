"""
CRUD operations for database interaction.

Encapsulating database access in separate functions makes it easier to
reason about the behaviour of the application and to test components
independently of the web framework.
"""

import json
from sqlalchemy.orm import Session

from . import models


def get_article(db: Session, article_id: int) -> models.Article | None:
    """Fetch a single article by its primary key."""
    return db.query(models.Article).filter(models.Article.id == article_id).first()


def get_article_by_url(db: Session, url: str) -> models.Article | None:
    """Return an article if a record with the given URL already exists."""
    return db.query(models.Article).filter(models.Article.url == url).first()


def get_articles(db: Session, skip: int = 0, limit: int = 100) -> list[models.Article]:
    """List articles with pagination."""
    return db.query(models.Article).offset(skip).limit(limit).all()


def create_article(db: Session, data: dict) -> models.Article:
    """Create a new article if one with the same URL does not exist.

    Articles are deduplicated on URL to avoid inserting the same
    story multiple times. If a duplicate exists the existing
    article is returned untouched.
    """
    existing = get_article_by_url(db, data.get("url"))
    if existing:
        return existing
    
    # Convert lists to JSON strings for TEXT storage
    if 'images' in data and isinstance(data['images'], list):
        data['images'] = json.dumps(data['images'])
    elif 'images' not in data:
        data['images'] = "[]"
        
    if 'videos' in data and isinstance(data['videos'], list):
        data['videos'] = json.dumps(data['videos'])
    elif 'videos' not in data:
        data['videos'] = "[]"
        
    article = models.Article(**data)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article