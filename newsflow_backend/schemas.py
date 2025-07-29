"""
Pydantic schemas for the NewsFlow AI Editor.

Enhanced schemas that support:
- Article data with media assets (images, videos)
- Validation and serialization for API endpoints
- Clean separation between create/read operations
"""

from typing import Optional, List
from enum import Enum
from datetime import datetime

from pydantic import BaseModel

class ScrapingMethod(str, Enum):
    REQUESTS = "requests"
    REQUESTS_ADVANCED = "requests_advanced"
    SCRAPY = "scrapy"
    INTELLIGENT = "intelligent"

class ArticleBase(BaseModel):
    title: str
    url: str
    content: str
    images: Optional[List[str]] = []
    videos: Optional[List[str]] = []

class ArticleCreate(ArticleBase):
    """Schema për krijimin e një artikulli të ri me media assets."""
    pass

class Article(ArticleBase):
    """Schema për kthimin e një artikulli përmes API me media të përfshirë."""
    id: int
    content_processed: Optional[str] = None
    status: str
    wordpress_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Updated for Pydantic v2

class EditInstruction(BaseModel):
    """Schema që përfshin një udhëzim të lirë për redaktim."""
    text: str

class ScrapeRequest(BaseModel):
    """Schema për kërkesën e scraping me një URL dhe metodën e zgjedhur."""
    url: str
    method: ScrapingMethod = ScrapingMethod.REQUESTS  # Default në requests