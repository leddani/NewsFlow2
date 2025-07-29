#!/usr/bin/env python3
"""
Scrapy Simple Engine për NewsFlow AI Editor

Version i thjeshtuar i Scrapy që punon pa reactor kompleks
"""

import logging
import subprocess
import tempfile
import json
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def scrape_with_scrapy_simple(url: str) -> List[Dict[str, Any]]:
    """Scrape me Scrapy duke përdorur një qasje të thjeshtë"""
    try:
        logger.info(f"🕷️ Scrapy Simple: Duke filluar scraping për {url}")
        
        # Krioj një spider file të përkohshëm
        spider_code = f'''
import scrapy
import json
import sys
from urllib.parse import urljoin

class SimpleNewsSpider(scrapy.Spider):
    name = 'simple_news'
    start_urls = ['{url}']
    
    def __init__(self):
        self.results = []
    
    def parse(self, response):
        # Ekstrakto titullin
        title_selectors = [
            'h1::text',
            'title::text',
            '.article-title::text',
            '.post-title::text'
        ]
        
        title = "Titull i panjohur"
        for selector in title_selectors:
            found_title = response.css(selector).get()
            if found_title and len(found_title.strip()) > 5:
                title = found_title.strip()
                break
        
        # Ekstrakto përmbajtjen
        content_selectors = [
            '.article-content p::text',
            '.post-content p::text',
            '.content p::text',
            'article p::text',
            'p::text'
        ]
        
        content_parts = []
        for selector in content_selectors:
            texts = response.css(selector).getall()
            content_parts.extend([t.strip() for t in texts if t.strip() and len(t.strip()) > 10])
            if len(' '.join(content_parts)) > 200:
                break
        
                 content = ' '.join(content_parts) if content_parts else "Permbajtje e shkurter"
        
        # Ekstrakto imazhet
        images = []
        img_selectors = ['img::attr(src)', '.article img::attr(src)']
        for selector in img_selectors:
            img_urls = response.css(selector).getall()
            for img_url in img_urls:
                if img_url:
                    full_url = urljoin(response.url, img_url)
                    if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        images.append(full_url)
        
        # Ekstrakto video
        videos = []
        video_selectors = [
            'iframe[src*="youtube.com"]::attr(src)',
            'a[href*="youtube.com"]::attr(href)'
        ]
        for selector in video_selectors:
            video_urls = response.css(selector).getall()
            videos.extend([url for url in video_urls if url])
        
        # Ruaj rezultatin
        article = {{
            'title': title,
            'url': response.url,
            'content': content,
            'images': list(set(images))[:5],
            'videos': list(set(videos))[:3]
        }}
        
        self.results.append(article)
        
        # Print rezultati në JSON format
        print("SCRAPY_RESULT_START")
        print(json.dumps(self.results))
        print("SCRAPY_RESULT_END")
'''
        
        # Ruaj spider-in në file të përkohshëm
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(spider_code)
            spider_file = f.name
        
        try:
            # Run Scrapy si subprocess
            cmd = [
                'python', '-m', 'scrapy', 'runspider', spider_file,
                '-s', 'LOG_LEVEL=ERROR',  # Minimize logs
                '-s', 'ROBOTSTXT_OBEY=False',
                '-s', 'DOWNLOAD_DELAY=1',
                '-s', 'USER_AGENT=NewsFlow-AI-Editor'
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60,  # 60 sekonda timeout
                cwd=os.getcwd()
            )
            
            # Parse rezultatin
            if result.returncode == 0:
                output = result.stdout
                
                # Gjej rezultatin JSON
                start_marker = "SCRAPY_RESULT_START"
                end_marker = "SCRAPY_RESULT_END"
                
                if start_marker in output and end_marker in output:
                    start_idx = output.find(start_marker) + len(start_marker)
                    end_idx = output.find(end_marker)
                    json_str = output[start_idx:end_idx].strip()
                    
                    try:
                        articles = json.loads(json_str)
                        logger.info(f"✅ Scrapy Simple: Gjeti {len(articles)} artikuj")
                        return articles
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON decode error: {e}")
                        logger.error(f"Raw output: {json_str}")
                
                logger.warning("⚠️ Scrapy Simple: Nuk gjeti rezultate të vlefshme")
                return []
            else:
                logger.error(f"❌ Scrapy Simple error: {result.stderr}")
                return []
                
        finally:
            # Clean up temp file
            try:
                os.unlink(spider_file)
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Scrapy Simple exception: {e}")
        return []


def test_scrapy_simple():
    """Test function për Scrapy Simple"""
    test_url = "https://www.balkanweb.com/"
    print(f"🧪 Testing Scrapy Simple with: {test_url}")
    
    results = scrape_with_scrapy_simple(test_url)
    
    print(f"📊 Results: {len(results)} articles found")
    for i, article in enumerate(results, 1):
        print(f"   {i}. {article.get('title', 'N/A')[:50]}...")
        print(f"      Content: {len(article.get('content', ''))} chars")
        print(f"      Images: {len(article.get('images', []))}")
        print(f"      Videos: {len(article.get('videos', []))}")


if __name__ == "__main__":
    test_scrapy_simple() 