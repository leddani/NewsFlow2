#!/usr/bin/env python3
"""
Scrapy Engine për NewsFlow AI Editor

Modul i ri për scraping me Scrapy framework
Integrohet me sistemin ekzistues pa prishur asgjë.
"""

import json
import logging
import tempfile
import os
from typing import List, Dict, Any, Optional
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import Spider, Request
from scrapy.http import Response
from urllib.parse import urljoin, urlparse
import re
from twisted.internet import reactor, defer

logger = logging.getLogger(__name__)

class NewsSpider(Spider):
    """Spider i personalizuar për scraping lajmesh"""
    name = 'news_spider'
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []
        self.scraped_articles = []
        
    def parse(self, response: Response):
        """Parse faqen kryesore dhe gjen artikujt"""
        try:
            # Gjen linqet e artikujve
            article_links = self.extract_article_links(response)
            
            # Nëse nuk gjejn linqe, provo të marrësh përmbajtjen direkt
            if not article_links:
                article = self.extract_single_article(response)
                if article:
                    self.scraped_articles.append(article)
                return
            
            # Parse çdo artikull
            for link in article_links[:10]:  # Limito në 10 artikuj
                full_url = urljoin(response.url, link)
                yield Request(url=full_url, callback=self.parse_article)
                
        except Exception as e:
            logger.error(f"Error në parsing: {e}")
    
    def extract_article_links(self, response: Response) -> List[str]:
        """Gjen linqet e artikujve në faqe"""
        links = []
        
        # Selektorë të ndryshëm për artikuj
        selectors = [
            'a[href*="/article/"]::attr(href)',
            'a[href*="/news/"]::attr(href)',
            'a[href*="/post/"]::attr(href)',
            'a[href*="/lajme/"]::attr(href)',
            'a[href*="/aktualitet/"]::attr(href)',
            'article a::attr(href)',
            '.article a::attr(href)',
            '.news a::attr(href)',
            '.post a::attr(href)',
            'h1 a::attr(href)',
            'h2 a::attr(href)',
            'h3 a::attr(href)',
        ]
        
        for selector in selectors:
            found_links = response.css(selector).getall()
            links.extend(found_links)
        
        # Filtro linqet e vlefshëm
        valid_links = []
        for link in links:
            if link and not link.startswith('#') and not link.startswith('javascript:'):
                if 'http' not in link or response.url.split('/')[2] in link:
                    valid_links.append(link)
        
        return list(set(valid_links))  # Hiq duplikatet
    
    def extract_single_article(self, response: Response) -> Optional[Dict[str, Any]]:
        """Ekstrakto një artikull nga faqja aktuale"""
        try:
            title = self.extract_title(response)
            content = self.extract_content(response)
            images = self.extract_images(response)
            videos = self.extract_videos(response)
            
            if title and content:
                return {
                    'title': title,
                    'url': response.url,
                    'content': content,
                    'images': images,
                    'videos': videos
                }
        except Exception as e:
            logger.error(f"Error në ekstraktimin e artikullit: {e}")
        
        return None
    
    def parse_article(self, response: Response):
        """Parse një artikull individual"""
        try:
            article = self.extract_single_article(response)
            if article:
                self.scraped_articles.append(article)
                
        except Exception as e:
            logger.error(f"Error në parsing artikulli: {e}")
    
    def extract_title(self, response: Response) -> str:
        """Ekstrakto titullin e artikullit"""
        selectors = [
            'h1::text',
            'title::text',
            '.article-title::text',
            '.post-title::text',
            '.entry-title::text',
            '[class*="title"] h1::text',
            '[class*="headline"]::text',
        ]
        
        for selector in selectors:
            title = response.css(selector).get()
            if title:
                title = title.strip()
                if len(title) > 10:  # Filtro tituj shumë të shkurtër
                    return title
        
        return "Titull i panjohur"
    
    def extract_content(self, response: Response) -> str:
        """Ekstrakto përmbajtjen e artikullit"""
        selectors = [
            '.article-content::text',
            '.post-content::text',
            '.entry-content::text',
            '.content::text',
            '[class*="content"] p::text',
            'article p::text',
            '.article p::text',
            'main p::text',
            'p::text',
        ]
        
        content_parts = []
        for selector in selectors:
            texts = response.css(selector).getall()
            if texts:
                content_parts.extend([t.strip() for t in texts if t.strip()])
                if len(' '.join(content_parts)) > 200:  # Ndaloj kur kam mjaft përmbajtje
                    break
        
        content = ' '.join(content_parts)
        
        # Pastro përmbajtjen
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content if len(content) > 50 else "Përmbajtje e shkurtër"
    
    def extract_images(self, response: Response) -> List[str]:
        """Ekstrakto imazhet nga artikulli"""
        images = []
        
        selectors = [
            '.article img::attr(src)',
            '.content img::attr(src)',
            'article img::attr(src)',
            'img::attr(src)',
        ]
        
        for selector in selectors:
            img_urls = response.css(selector).getall()
            for img_url in img_urls:
                if img_url:
                    full_img_url = urljoin(response.url, img_url)
                    if self.is_valid_image(full_img_url):
                        images.append(full_img_url)
        
        return list(set(images))[:5]  # Maksimum 5 imazhe
    
    def extract_videos(self, response: Response) -> List[str]:
        """Ekstrakto video nga artikulli"""
        videos = []
        
        # YouTube embeddings
        youtube_selectors = [
            'iframe[src*="youtube.com"]::attr(src)',
            'iframe[src*="youtu.be"]::attr(src)',
            'a[href*="youtube.com"]::attr(href)',
            'a[href*="youtu.be"]::attr(href)',
        ]
        
        for selector in youtube_selectors:
            video_urls = response.css(selector).getall()
            videos.extend([url for url in video_urls if url])
        
        return list(set(videos))[:3]  # Maksimum 3 video
    
    def is_valid_image(self, url: str) -> bool:
        """Kontrollon nëse URL-ja është imazh i vlefshëm"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        url_lower = url.lower()
        
        # Kontrollo ekstensionin
        for ext in image_extensions:
            if ext in url_lower:
                return True
        
        # Kontrollo për fjalë kyçe të imazheve
        image_keywords = ['image', 'img', 'photo', 'picture']
        for keyword in image_keywords:
            if keyword in url_lower:
                return True
        
        return False


class ScrapyEngine:
    """Engine kryesor për Scrapy scraping"""
    
    def __init__(self):
        self.results = []
        
    def scrape_website(self, url: str, settings: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Scrape një website me Scrapy"""
        try:
            logger.info(f"🕷️ Scrapy: Duke filluar scraping për {url}")
            
            # Konfigurimi i Scrapy
            scrapy_settings = self.get_scrapy_settings(settings)
            
            # Krijoj procesin e crawler-it
            process = CrawlerProcess(scrapy_settings)
            
            # Rezultatet do të ruhen këtu
            self.results = []
            
            # Krijoj spider-in
            spider = NewsSpider(start_url=url)
            
            # Hook për të marrë rezultatet
            def spider_closed(spider, reason):
                self.results = spider.scraped_articles
                logger.info(f"🕷️ Scrapy: U mbyll spider-i. Gjeti {len(self.results)} artikuj")
            
            # Lidh signal-in
            from scrapy import signals
            process.crawl(NewsSpider, start_url=url)
            
            # Start crawler
            if not reactor.running:
                process.start(stop_after_crawl=True)
            else:
                # Nëse reactor-i është duke punuar, përdor deferred
                deferred = process.crawl(NewsSpider, start_url=url)
                deferred.addCallback(lambda _: spider_closed(spider, 'finished'))
            
            logger.info(f"✅ Scrapy: Mbaroi scraping për {url}")
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Scrapy Error: {e}")
            return []
    
    def get_scrapy_settings(self, custom_settings: Optional[Dict] = None) -> Dict:
        """Merr settings për Scrapy"""
        settings = {
            'USER_AGENT': 'NewsFlow-AI-Editor (+https://newsflow.ai)',
            'ROBOTSTXT_OBEY': False,  # Mos respekto robots.txt për lajmet
            'DOWNLOAD_DELAY': 1,      # 1 sekondë delay midis request-eve
            'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
            'CONCURRENT_REQUESTS': 1,  # Një request në herë
            'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
            'DOWNLOAD_TIMEOUT': 30,
            'RETRY_TIMES': 2,
            'LOG_LEVEL': 'ERROR',     # Minimizo log-et
            'TELNETCONSOLE_ENABLED': False,
            'COOKIES_ENABLED': True,
            'HTTPERROR_ALLOWED_CODES': [404, 403],  # Lejoj disa error codes
        }
        
        if custom_settings:
            settings.update(custom_settings)
        
        return settings


# Instanca globale e Scrapy Engine
scrapy_engine = ScrapyEngine()

def scrape_with_scrapy(url: str, settings: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Funksion helper për scraping me Scrapy"""
    return scrapy_engine.scrape_website(url, settings) 