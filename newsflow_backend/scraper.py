"""
Scraping engine for NewsFlow AI Editor.

Enhanced version that extracts:
- Full article title (cleaned from website names)
- Article content with embedded images
- Related video/YouTube links
- NO advertisements or source website references
"""

from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

def extract_images_and_media(soup, base_url: str) -> Dict[str, List[str]]:
    """Extract relevant images and media links from article content."""
    images = []
    videos = []
    
    # Find images in article content (avoid ads, logos, etc.)
    img_tags = soup.find_all('img')
    for img in img_tags:
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if src:
            # Skip small images (likely ads or icons)
            width = img.get('width', '0')
            height = img.get('height', '0')
            try:
                if width and height and (int(width) < 200 or int(height) < 150):
                    continue
            except:
                pass
            
            # Skip images with ad-related classes or alt text
            img_class = ' '.join(img.get('class', []))
            alt_text = img.get('alt', '').lower()
            
            if any(skip_word in img_class.lower() for skip_word in ['ad', 'banner', 'logo', 'header', 'footer', 'sidebar']):
                continue
            if any(skip_word in alt_text for skip_word in ['reklama', 'ad', 'banner', 'logo']):
                continue
            
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            
            # Only include image URLs
            if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                images.append(src)
    
    # Find YouTube and video links
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if any(domain in href for domain in ['youtube.com', 'youtu.be', 'vimeo.com']):
            videos.append(href)
    
    # Find embedded videos
    iframes = soup.find_all('iframe')
    for iframe in iframes:
        src = iframe.get('src', '')
        if any(domain in src for domain in ['youtube.com', 'youtu.be', 'vimeo.com']):
            videos.append(src)
    
    return {
        'images': images[:5],  # Limit to first 5 relevant images
        'videos': videos[:3]   # Limit to first 3 video links
    }

def clean_content_from_source_references(content: str, url: str) -> str:
    """Remove website names and source references from content."""
    domain = urlparse(url).netloc
    website_name = domain.replace('www.', '').replace('.com', '').replace('.al', '').replace('.net', '').replace('.org', '')
    
    # Remove common source patterns
    patterns_to_remove = [
        rf'\b{re.escape(website_name)}\b',
        rf'\b{re.escape(domain)}\b',
        r'\b(burim|source|nga|sipas)\s*[:]\s*\w+\.\w+',
        r'\b(lexo më shumë|më shumë në|shiko edhe)\s*[:]\s*\w+\.\w+',
        r'\b(foto|video|image)\s*[:]\s*\w+\.\w+',
        r'\b\w+\.(com|al|net|org|info)\b',
        r'©\s*\w+',
        r'All rights reserved',
        r'Të drejtat e rezervuara',
        r'\bDate\s*[:]\s*\d+',
        r'\bAuthor\s*[:]\s*\w+',
        r'\bKategori\s*[:]\s*\w+',
        r'\bTags\s*[:]\s*\w+',
        r'\d+\s*komente?',
        r'Share\s*[:]\s*',
        r'Facebook\s*\|\s*Twitter',
        r'Ndaj në\s*[:]\s*'
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Clean up whitespace
    content = ' '.join(content.split())
    return content

def scrape_with_requests(url: str) -> List[Dict[str, str]]:
    """Scrape një artikull duke përdorur requests + BeautifulSoup me headers të përmirësuar."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Përpiqemi të marrim titullin nga disa vende të ndryshme
        title = None
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        elif soup.find('meta', property='og:title'):
            title = soup.find('meta', property='og:title')['content']
        
        if not title:
            title = 'Titull i panjohur'
        
        # Clean title from website references
        title = clean_content_from_source_references(title, url)
        
        # Extract images and media (basic version)
        media_data = extract_images_and_media(soup, url)
        
        # Marrim përmbajtjen nga paragrafët, por edhe nga div-et që mund të përmbajnë tekst
        content_parts = []
        
        # Shto paragrafët
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 20:  # Vetëm paragrafët me tekst të gjatë
                content_parts.append(text)
        
        # Nëse nuk ka paragrafë, provo div-et
        if not content_parts:
            for div in soup.find_all('div'):
                text = div.get_text().strip()
                if text and len(text) > 50:  # Vetëm div-et me tekst të gjatë
                    content_parts.append(text)
        
        content = ' '.join(content_parts)
        
        if not content:
            content = 'Përmbajtja nuk u gjet.'
        
        # Clean content from source references
        content = clean_content_from_source_references(content, url)
        
        return [{
            "title": title,
            "url": url,
            "content": content,
            "images": media_data['images'],
            "videos": media_data['videos']
        }]
    except Exception as e:
        return [{
            "title": "Scraping Failed",
            "url": url,
            "content": f"Gabim gjatë scraping me requests: {str(e)}",
            "images": [],
            "videos": []
        }]

def scrape_with_requests_advanced(url: str) -> List[Dict[str, str]]:
    """Scrape të avancuar për faqet që kanë mbrojtje anti-bot dhe ekstraktim të plotë të mediave."""
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "sq-AL,sq;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        })
        
        domain = url.split('/')[2]
        home_url = f"https://{domain}"
        try:
            session.get(home_url, timeout=10)
        except:
            pass
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title - clean it from website name thoroughly
        title = None
        if soup.title:
            title = soup.title.string.strip()
            # Remove website name from title - try multiple separators
            for separator in [' – ', ' - ', ' | ', ' :: ', ' | ', '|', ' – ', ' — ']:
                if separator in title:
                    parts = title.split(separator)
                    # Take the first part (actual article title)
                    title = parts[0].strip()
                    break
            
            # Additional cleaning for common patterns
            title_clean_patterns = [
                r'^Kreu\s*[-–—]\s*',
                r'^Home\s*[-–—]\s*',
                r'^News\s*[-–—]\s*',
                r'^Lajme\s*[-–—]\s*',
                r'\s*[-–—]\s*\w+\.(com|al|net|org).*$',
                r'\s*\|\s*\w+\.(com|al|net|org).*$'
            ]
            
            for pattern in title_clean_patterns:
                title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
                
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        elif soup.find('meta', property='og:title'):
            title = soup.find('meta', property='og:title')['content']
        elif soup.find('meta', attrs={'name': 'title'}):
            title = soup.find('meta', attrs={'name': 'title'})['content']
        
        if not title:
            title = 'Titull i panjohur'
        
        # Clean title from any remaining website references
        title = clean_content_from_source_references(title, url)
        
        # Extract images and media
        media_data = extract_images_and_media(soup, url)
        
        # Extract content with better selectors and ad filtering
        content_parts = []
        
        # Remove unwanted elements before content extraction
        for unwanted in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            unwanted.decompose()
        
        # Remove ad-related elements
        ad_selectors = [
            '.ad', '.ads', '.advertisement', '.banner', '.promo', '.sponsored',
            '[class*="ad-"]', '[class*="ads-"]', '[id*="ad-"]', '[id*="ads-"]',
            '.sidebar', '.widget', '.comments', '.metadata', '.share-buttons',
            '.social-share', '.related-posts', '.author-bio', '.newsletter'
        ]
        
        for selector in ad_selectors:
            for elem in soup.select(selector):
                elem.decompose()
        
        # Try different article content selectors
        content_selectors = [
            '.post-content',       # shkodrazone.com dhe shumë faqe të tjera
            '.entry-content',      # WordPress standard
            '.article-content',    # News sites
            '.content-area',       # General content
            'article .content',    # Semantic HTML
            '.post-body',          # Blog posts
            '.story-body',         # News articles
            '[class*="content"]',  # Any class containing "content"
            'main p',              # Main content paragraphs
            'article p'            # Article paragraphs
        ]
        
        content_found = False
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                for elem in elements:
                    text = elem.get_text().strip()
                    if text and len(text) > 50:  # Only meaningful content
                        content_parts.append(text)
                        content_found = True
                if content_found:
                    break
        
        # Fallback: try all paragraphs but filter out unwanted content
        if not content_parts:
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                # Skip paragraphs with metadata, ads, or navigation
                skip_keywords = [
                    'komente', 'date:', 'author:', 'tags:', 'kategori', 'share', 
                    'facebook', 'twitter', 'më shumë', 'lexo', 'shiko', 'burim',
                    'copyright', '©', 'rights reserved', 'të drejtat'
                ]
                if text and len(text) > 30 and not any(skip in text.lower() for skip in skip_keywords):
                    content_parts.append(text)
        
        # Clean and join content
        if content_parts:
            content = ' '.join(content_parts)
            # Remove excessive whitespace
            content = ' '.join(content.split())
            # Clean from source references
            content = clean_content_from_source_references(content, url)
        else:
            content = 'Përmbajtja nuk u gjet.'
        
        # Format the complete article with media
        article_data = {
            "title": title,
            "url": url,
            "content": content,
            "images": media_data['images'],
            "videos": media_data['videos']
        }
        
        return [article_data]
        
    except Exception as e:
        return [{
            "title": "Gabim në scraping",
            "url": url,
            "content": f"Gabim gjatë scraping me requests advanced: {str(e)}",
            "images": [],
            "videos": []
        }]

def scrape_articles(url: str, method: str = "requests") -> List[Dict[str, str]]:
    """Scrape një artikull nga një URL e dhënë duke përdorur metodën e zgjedhur."""
    if method == "intelligent":
        # Përdor Scrapy Engine të Inteligjentë
        try:
            from .scrapy_intelligent import scrape_with_intelligent_scrapy
            return scrape_with_intelligent_scrapy(url)
        except ImportError as e:
            print(f"⚠️ Scrapy Intelligent nuk është i disponueshëm: {e}. Po përdor requests...")
            return scrape_with_requests(url)
        except Exception as e:
            print(f"❌ Scrapy Intelligent error: {e}. Po përdor requests...")
            return scrape_with_requests(url)
    elif method == "scrapy":
        # Përdor Scrapy engine të thjeshtë
        try:
            import scrapy
            from scrapy.http import HtmlResponse
            import requests
            
            # Merr HTML-in me requests dhe process me Scrapy selectors
            headers = {
                'User-Agent': 'NewsFlow-AI-Editor (+https://newsflow.ai)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'sq,en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            
            # Krijon Scrapy response object
            scrapy_response = HtmlResponse(url=url, body=response.content, encoding='utf-8')
            
            # Ekstrakto me Scrapy selectors
            title_selectors = [
                'h1::text',
                'title::text', 
                '.article-title::text',
                '.post-title::text',
                '.entry-title::text'
            ]
            
            title = "Scrapy Scraping"
            for selector in title_selectors:
                found_title = scrapy_response.css(selector).get()
                if found_title and len(found_title.strip()) > 5:
                    title = found_title.strip()
                    break
            
            # Ekstrakto përmbajtjen me Scrapy
            content_selectors = [
                '.article-content p::text',
                '.post-content p::text', 
                '.entry-content p::text',
                '.content p::text',
                'article p::text',
                'p::text'
            ]
            
            content_parts = []
            for selector in content_selectors:
                texts = scrapy_response.css(selector).getall()
                content_parts.extend([t.strip() for t in texts if t.strip() and len(t.strip()) > 10])
                if len(' '.join(content_parts)) > 300:
                    break
            
            content = ' '.join(content_parts) if content_parts else "Permbajtje nga Scrapy"
            
            # Ekstrakto imazhet
            images = []
            img_selectors = ['img::attr(src)', '.article img::attr(src)', 'article img::attr(src)']
            for selector in img_selectors:
                img_urls = scrapy_response.css(selector).getall()
                for img_url in img_urls:
                    if img_url:
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        elif img_url.startswith('/'):
                            from urllib.parse import urljoin
                            img_url = urljoin(url, img_url)
                        
                        if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                            images.append(img_url)
            
            # Ekstrakto videos
            videos = []
            video_selectors = [
                'iframe[src*="youtube.com"]::attr(src)',
                'iframe[src*="youtu.be"]::attr(src)',
                'a[href*="youtube.com"]::attr(href)',
                'a[href*="youtu.be"]::attr(href)'
            ]
            for selector in video_selectors:
                video_urls = scrapy_response.css(selector).getall()
                videos.extend([v for v in video_urls if v])
            
            return [{
                "title": title,
                "url": url,
                "content": content,
                "images": list(set(images))[:5],
                "videos": list(set(videos))[:3]
            }]
            
        except ImportError:
            # Fallback nëse Scrapy nuk është i instaluar
            print("⚠️ Scrapy nuk është i instaluar. Po përdor requests...")
            return scrape_with_requests(url)
        except Exception as e:
            print(f"❌ Scrapy error: {e}. Po përdor requests...")
            return scrape_with_requests(url)
    elif method == "requests_advanced":
        return scrape_with_requests_advanced(url)
    else:
        # Default: provo metodën e thjeshtë së pari
        result = scrape_with_requests(url)
        # Nëse dështon (403, 404, etj.), provo metodën e avancuar automatikisht
        if result and "Scraping Failed" in result[0].get("title", ""):
            return scrape_with_requests_advanced(url)
        return result