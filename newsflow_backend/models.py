"""
SQLAlchemy models for the NewsFlow AI Editor.

Enhanced Article model that supports:
- Basic article data (title, url, content)
- LLM processed content  
- Media assets (images and videos)
- Workflow status tracking
"""

import json
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

from .database import Base


class Article(Base):
    """A scraped news article with media assets awaiting review and publication."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    # Title of the article
    title = Column(String, index=True)
    # Original URL where the article was found
    url = Column(String, unique=True, index=True)
    # Raw scraped content (may include HTML tags)
    content = Column(Text)
    # Processed content returned from the LLM (e.g. summarised or rephrased)
    content_processed = Column(Text, nullable=True)
    # List of image URLs extracted from the article (stored as JSON text)
    _images = Column("images", Text, nullable=True, default="[]")
    # List of video/YouTube URLs related to the article (stored as JSON text)  
    _videos = Column("videos", Text, nullable=True, default="[]")
    # Workflow status: scraped, edited, published, rejected, etc.
    status = Column(String, default="scraped")
    # ID of the corresponding post in WordPress (if published)
    wordpress_id = Column(String, nullable=True)
    # Timestamp of creation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    @hybrid_property
    def images(self):
        """Return images as a list."""
        if self._images:
            try:
                return json.loads(self._images)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @images.setter
    def images(self, value):
        """Set images as JSON string."""
        if isinstance(value, list):
            self._images = json.dumps(value)
        elif isinstance(value, str):
            self._images = value
        else:
            self._images = "[]"
    
    @hybrid_property
    def videos(self):
        """Return videos as a list."""
        if self._videos:
            try:
                return json.loads(self._videos)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @videos.setter
    def videos(self, value):
        """Set videos as JSON string."""
        if isinstance(value, list):
            self._videos = json.dumps(value)
        elif isinstance(value, str):
            self._videos = value
        else:
            self._videos = "[]"