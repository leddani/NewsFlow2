#!/usr/bin/env python3
"""
Scrapy Engine i Inteligjentë për NewsFlow AI Editor

Engine i ri që e kupton se cilat janë lajmet më të reja:
1. Gjen të gjitha lajmet nga homepage
2. I organizon sipas pozicionit (lajmet e para janë më të reja)
3. Kontrollon në databazë se cilat i ka parë tashmë
4. Ndalon kur gjen lajme të njohura
5. Kthen vetëm lajmet e reja
"""

import json
import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import crud

logger = logging.getLogger(__name__)

class IntelligentNewsScraper:
    """Scrapy Engine i inteligjentë që e kupton lajmet më të reja"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'NewsFlow-AI-Editor (+https://newsflow.ai)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'sq,en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def scrape_intelligent(self, base_url: str, max_articles: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape intelligent që gjen vetëm lajmet e reja
        
        Args:
            base_url: URL-ja e faqes kryesore (p.sh. https://www.balkanweb.com/)
            max_articles: Numri maksimal i artikujve për t'u kontrolluar
            
        Returns:
            Lista e lajmeve të reja
        """
        try:
            logger.info(f"🧠 Scrapy Intelligent: Duke filluar për {base_url}")
            
            # Hapi 1: Merr homepage-in
            response = requests.get(base_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Hapi 2: Gjen të gjitha linqet e lajmeve
            news_links = self._extract_news_links(soup, base_url)
            logger.info(f"🔍 Gjeta {len(news_links)} linqe potenciale lajmesh")
            
            if not news_links:
                logger.warning(f"⚠️ Nuk gjeta linqe lajmesh në {base_url}")
                return []
            
            # Hapi 3: Kontrollo dhe scrape vetëm lajmet e reja
            new_articles = []
            checked_count = 0
            
            for i, link in enumerate(news_links[:max_articles]):
                checked_count += 1
                
                # Kontrollo nëse ky artikull ekziston në databazë
                if self._article_exists_in_database(link):
                    logger.info(f"📚 Artikulli {i+1} ekziston në DB: {link[:60]}...")
                    logger.info(f"🛑 NDALOJ këtu - kam arritur lajme të njohura (pozicioni {i+1})")
                    break
                
                # Artikull i ri - scrape-o
                logger.info(f"🆕 Artikull i ri {i+1}: {link[:60]}...")
                article_data = self._scrape_single_article(link)
                
                if article_data:
                    new_articles.append(article_data)
                    logger.info(f"✅ Scrape u krye për: {article_data['title'][:50]}...")
            
            logger.info(f"🎯 Scrapy Intelligent REZULTATI:")
            logger.info(f"   📊 Artikuj të kontrolluar: {checked_count}")
            logger.info(f"   🆕 Artikuj të rinj: {len(new_articles)}")
            
            return new_articles
            
        except Exception as e:
            logger.error(f"❌ Scrapy Intelligent error për {base_url}: {e}")
            return []
    
    def _extract_news_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Ekstrakton të gjitha linqet e lajmeve nga homepage, të organizuara sipas pozicionit"""
        
        # Selektorë të ndryshëm për lajme (të organizuar sipas prioritetit)
        news_selectors = [
            # Selektorë të përbashkët për lajme
            'article a[href]',
            '.article a[href]',
            '.news a[href]',
            '.post a[href]',
            '.entry a[href]',
            
            # Selektorë për tituj
            'h1 a[href]',
            'h2 a[href]',
            'h3 a[href]',
            
            # Selektorë të specializuar
            '.latest-news a[href]',
            '.news-item a[href]',
            '.story a[href]',
            '.headline a[href]',
            
            # Selektorë të përgjithshëm (si fallback)
            'a[href*="/article/"]',
            'a[href*="/news/"]',
            'a[href*="/lajme/"]',
            'a[href*="/aktualitet/"]',
        ]
        
        found_links = []
        domain = urlparse(base_url).netloc
        
        for selector in news_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and self._is_valid_news_link(href, domain):
                        full_url = urljoin(base_url, href)
                        if full_url not in found_links:
                            found_links.append(full_url)
            except Exception as e:
                logger.debug(f"Selector error {selector}: {e}")
        
        # Limitoj dhe kthej linqet (të organizuara sipas pozicionit në homepage)
        return found_links[:20]  # Maksimum 20 linqe për performancë
    
    def _is_valid_news_link(self, href: str, domain: str) -> bool:
        """Kontrollon nëse një link është link i vlefshëm lajmi"""
        
        if not href or href.startswith('#') or href.startswith('javascript:'):
            return False
        
        # Përjashto llojet e tjera të faqeve
        exclude_patterns = [
            '/category/', '/tag/', '/author/', '/search/',
            '/contact/', '/about/', '/privacy/', '/terms/',
            '.pdf', '.jpg', '.png', '.gif', '.mp4', '.mp3',
            'mailto:', 'tel:', 'facebook.com', 'twitter.com',
            'instagram.com', 'youtube.com', '#comment'
        ]
        
        for pattern in exclude_patterns:
            if pattern in href.lower():
                return False
        
        # Prefero linqet e brendshëm
        if href.startswith('http'):
            return domain in href
        
        return True
    
    def _article_exists_in_database(self, url: str) -> bool:
        """Kontrollon nëse një artikull ekziston në databazë"""
        try:
            db = SessionLocal()
            try:
                existing_article = crud.get_article_by_url(db, url)
                return existing_article is not None
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"Database check error për {url}: {e}")
            return False
    
    def _scrape_single_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape një artikull të vetëm"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ekstrakto title
            title = self._extract_title(soup)
            
            # Ekstrakto content
            content = self._extract_content(soup)
            
            # Ekstrakto images dhe videos
            images = self._extract_images(soup, url)
            videos = self._extract_videos(soup)
            
            if not title or not content:
                logger.warning(f"⚠️ Title ose content bosh për {url}")
                return None
            
            return {
                'title': title,
                'url': url,
                'content': content,
                'images': images,
                'videos': videos
            }
            
        except Exception as e:
            logger.error(f"❌ Error scraping single article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Ekstrakton titullin e artikullit"""
        
        # Selektorë të ndryshëm për title
        title_selectors = [
            'h1',
            '.article-title',
            '.post-title', 
            '.entry-title',
            'title',
            '[property="og:title"]',
            '[name="title"]'
        ]
        
        for selector in title_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text().strip() if element.name != 'meta' else element.get('content', '')
                    if title and len(title) > 10:
                        # Pastro nga emrat e website-it
                        title = self._clean_title(title)
                        return title
            except Exception:
                continue
        
        return "Titull i panjohur"
    
    def _clean_title(self, title: str) -> str:
        """Pastron titullin nga emrat e website-it"""
        
        # Hiq separatorët dhe emrat e website-it
        for separator in [' – ', ' - ', ' | ', ' :: ', ' — ']:
            if separator in title:
                parts = title.split(separator)
                title = parts[0].strip()  # Merr vetëm pjesën e parë
                break
        
        # Hiq pattern-et e zakonshme
        patterns_to_remove = [
            r'^(Kreu|Home|News|Lajme)\s*[-–—]\s*',
            r'\s*[-–—]\s*\w+\.(com|al|net|org).*$',
            r'\s*\|\s*\w+\.(com|al|net|org).*$'
        ]
        
        for pattern in patterns_to_remove:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
        
        return title
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Ekstrakton përmbajtjen e artikullit"""
        
        # Selektorë për content
        content_selectors = [
            '.article-content',
            '.post-content',
            '.entry-content', 
            '.content',
            'article',
            '.story-body',
            '.news-content'
        ]
        
        content_parts = []
        
        for selector in content_selectors:
            try:
                container = soup.select_one(selector)
                if container:
                    # Merr të gjitha paragrafët
                    paragraphs = container.find_all('p')
                    for p in paragraphs:
                        text = p.get_text().strip()
                        if text and len(text) > 20:
                            content_parts.append(text)
                    
                    if content_parts:
                        break
            except Exception:
                continue
        
        # Fallback: merr të gjitha paragrafët nga faqja
        if not content_parts:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20:
                    content_parts.append(text)
        
        content = ' '.join(content_parts)
        return content if len(content) > 50 else "Përmbajtje e shkurtër"
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Ekstrakton imazhet nga artikulli"""
        images = []
        
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src:
                full_img_url = urljoin(base_url, src)
                if self._is_valid_image_url(full_img_url):
                    images.append(full_img_url)
        
        return list(set(images))[:5]  # Maksimum 5 imazhe
    
    def _extract_videos(self, soup: BeautifulSoup) -> List[str]:
        """Ekstrakton videos nga artikulli"""
        videos = []
        
        # YouTube dhe Vimeo embeddings
        video_selectors = [
            'iframe[src*="youtube.com"]',
            'iframe[src*="youtu.be"]',
            'iframe[src*="vimeo.com"]',
            'a[href*="youtube.com"]',
            'a[href*="youtu.be"]'
        ]
        
        for selector in video_selectors:
            elements = soup.select(selector)
            for element in elements:
                url = element.get('src') or element.get('href')
                if url:
                    videos.append(url)
        
        return list(set(videos))[:3]  # Maksimum 3 video
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Kontrollon nëse URL-ja është imazh i vlefshëm"""
        if not url:
            return False
        
        # Kontrollo ekstensionin
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        url_lower = url.lower()
        
        for ext in image_extensions:
            if ext in url_lower:
                return True
        
        # Kontrollo për fjalë kyçe
        if any(keyword in url_lower for keyword in ['image', 'img', 'photo', 'picture']):
            return True
        
        return False


# Instanca globale
intelligent_scraper = IntelligentNewsScraper()

def scrape_with_intelligent_scrapy(url: str, max_articles: int = 10) -> List[Dict[str, Any]]:
    """
    Funksion helper për scraping të inteligjentë
    
    Args:
        url: URL-ja e faqes kryesore
        max_articles: Numri maksimal i artikujve për t'u kontrolluar
        
    Returns:
        Lista e lajmeve të reja
    """
    return intelligent_scraper.scrape_intelligent(url, max_articles) 