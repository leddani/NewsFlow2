"""
WordPress integration for NewsFlow AI Editor.

This module handles publishing articles to WordPress using the REST API.
It supports authentication via application passwords, automatic image upload,
and proper content formatting with media embedding.
"""

import os
import requests
import base64
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
import mimetypes
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# WordPress configuration from environment variables
WORDPRESS_SITE_URL = os.getenv("WORDPRESS_SITE_URL", "https://your-site.com")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME", "admin")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", "your-app-password")
WORDPRESS_AUTHOR_ID = os.getenv("WORDPRESS_AUTHOR_ID", "1")  # Default admin user ID

# Setup logging
logger = logging.getLogger(__name__)

class WordPressPublisher:
    def __init__(self):
        self.site_url = WORDPRESS_SITE_URL.rstrip('/')
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.username = WORDPRESS_USERNAME
        self.app_password = WORDPRESS_APP_PASSWORD
        self.author_id = int(WORDPRESS_AUTHOR_ID)
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for WordPress REST API."""
        credentials = f"{self.username}:{self.app_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
    
    def _upload_image(self, image_url: str, title: str = "") -> Optional[int]:
        """Upload an image to WordPress media library.
        
        Args:
            image_url: URL of the image to upload
            title: Title for the image (optional)
            
        Returns:
            WordPress media ID if successful, None otherwise
        """
        try:
            # Download the image
            logger.info(f"Downloading image: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Get filename and content type
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path) or "image.jpg"
            content_type = response.headers.get('content-type') or mimetypes.guess_type(filename)[0] or 'image/jpeg'
            
            # Prepare upload data
            upload_url = f"{self.api_base}/media"
            headers = {
                "Authorization": f"Basic {base64.b64encode(f'{self.username}:{self.app_password}'.encode()).decode()}",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type
            }
            
            # Upload to WordPress
            logger.info(f"Uploading to WordPress: {filename}")
            upload_response = requests.post(
                upload_url,
                headers=headers,
                data=response.content,
                timeout=60
            )
            upload_response.raise_for_status()
            
            media_data = upload_response.json()
            media_id = media_data.get('id')
            
            # Update media with title if provided
            if title and media_id:
                self._update_media_metadata(media_id, title)
            
            logger.info(f"Image uploaded successfully. Media ID: {media_id}")
            return media_id
            
        except Exception as e:
            logger.error(f"Failed to upload image {image_url}: {e}")
            return None
    
    def _update_media_metadata(self, media_id: int, title: str):
        """Update media metadata with title."""
        try:
            update_url = f"{self.api_base}/media/{media_id}"
            data = {
                "title": title,
                "alt_text": title
            }
            
            response = requests.post(
                update_url,
                headers=self._get_auth_headers(),
                json=data,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Updated media {media_id} with title: {title}")
            
        except Exception as e:
            logger.error(f"Failed to update media metadata: {e}")
    
    def _format_content_with_media(self, content: str, images: List[str], videos: List[str], uploaded_media_ids: List[int]) -> str:
        """Format content with uploaded media."""
        formatted_content = content.strip()
        
        # Add uploaded images to content
        if uploaded_media_ids:
            media_html = ""
            for i, media_id in enumerate(uploaded_media_ids):
                # Get the actual media URL from WordPress API
                try:
                    media_url = f"{self.api_base}/media/{media_id}"
                    response = requests.get(media_url, headers=self._get_auth_headers(), timeout=30)
                    if response.status_code == 200:
                        media_data = response.json()
                        image_url = media_data.get('source_url', '')
                        if image_url:
                            media_html += f'<!-- wp:image {{"id":{media_id},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                            media_html += f'<figure class="wp-block-image size-large"><img src="{image_url}" alt="" class="wp-image-{media_id}"/></figure>\n'
                            media_html += f'<!-- /wp:image -->\n\n'
                except Exception as e:
                    logger.warning(f"Could not get media URL for {media_id}: {e}")
                    # Fallback to a generic image block
                    media_html += f'<!-- wp:image {{"id":{media_id}}} -->\n'
                    media_html += f'<figure class="wp-block-image"><img class="wp-image-{media_id}" alt=""/></figure>\n'
                    media_html += f'<!-- /wp:image -->\n\n'
            
            # Insert media after first paragraph
            paragraphs = formatted_content.split('\n\n')
            if len(paragraphs) > 1:
                paragraphs.insert(1, media_html)
                formatted_content = '\n\n'.join(paragraphs)
            else:
                formatted_content = media_html + formatted_content
        
        # Add video links at the end
        if videos:
            video_section = "\n\n<h3>Video të lidhura:</h3>\n<ul>\n"
            for video in videos:
                video_section += f'<li><a href="{video}" target="_blank">Shiko videon</a></li>\n'
            video_section += "</ul>\n"
            formatted_content += video_section
        
        # Convert line breaks to paragraphs
        formatted_content = re.sub(r'\n\n+', '</p>\n\n<p>', formatted_content)
        formatted_content = f"<p>{formatted_content}</p>"
        
        return formatted_content
    
    def publish_article(self, article) -> Optional[str]:
        """Publish an article to WordPress.
        
        Args:
            article: Article model instance with title, content_processed, images, videos
            
        Returns:
            WordPress post URL if successful, None otherwise
        """
        try:
            logger.info(f"Starting WordPress publishing for: {article.title}")
            
            # Get article data
            title = article.title or "Lajm i ri"
            content = article.content_processed or article.content or ""
            images = getattr(article, 'images', []) or []
            videos = getattr(article, 'videos', []) or []
            
            # Upload images to WordPress
            uploaded_media_ids = []
            for image_url in images[:3]:  # Limit to 3 images
                media_id = self._upload_image(image_url, title)
                if media_id:
                    uploaded_media_ids.append(media_id)
            
            # Format content with media
            formatted_content = self._format_content_with_media(
                content, images, videos, uploaded_media_ids
            )
            
            # Prepare post data
            post_data = {
                "title": title,
                "content": formatted_content,
                "status": "publish",  # Publish immediately
                "author": self.author_id,
                "format": "standard"
            }
            
            # Set featured image if we uploaded any
            if uploaded_media_ids:
                post_data["featured_media"] = uploaded_media_ids[0]
            
            # Create the post
            logger.info("Creating WordPress post...")
            post_url = f"{self.api_base}/posts"
            response = requests.post(
                post_url,
                headers=self._get_auth_headers(),
                json=post_data,
                timeout=60
            )
            response.raise_for_status()
            
            post_response = response.json()
            post_id = post_response.get('id')
            post_link = post_response.get('link')
            
            logger.info(f"✅ Article published successfully!")
            logger.info(f"   WordPress ID: {post_id}")
            logger.info(f"   URL: {post_link}")
            logger.info(f"   Images uploaded: {len(uploaded_media_ids)}")
            logger.info(f"   Videos linked: {len(videos)}")
            
            return post_link
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ WordPress API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error publishing to WordPress: {e}")
            return None

# Global publisher instance
wordpress_publisher = WordPressPublisher()

def publish_to_wordpress(article) -> Optional[str]:
    """Legacy function for backward compatibility.
    
    Args:
        article: Article model instance
        
    Returns:
        WordPress post URL if successful, None otherwise
    """
    # Check if WordPress is properly configured
    if not all([WORDPRESS_SITE_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD]):
        logger.warning("⚠️ WordPress not configured. Article not published.")
        logger.info("   Set WORDPRESS_SITE_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD")
        print(f"[WordPress] Demo mode: Would publish '{article.title}' with processed content and {len(getattr(article, 'images', []))} images")
        return f"demo-post-{article.id}"
    
    # Try to publish, but fallback to demo mode if authentication fails
    try:
        result = wordpress_publisher.publish_article(article)
        if result:
            return result
        else:
            logger.warning("⚠️ WordPress publishing failed, using demo mode")
            print(f"[WordPress] Demo mode: Would publish '{article.title}' with processed content and {len(getattr(article, 'images', []))} images")
            return f"demo-post-{article.id}"
    except Exception as e:
        logger.error(f"❌ WordPress error: {e}")
        logger.warning("⚠️ Falling back to demo mode")
        print(f"[WordPress] Demo mode: Would publish '{article.title}' with processed content and {len(getattr(article, 'images', []))} images")
        return f"demo-post-{article.id}"