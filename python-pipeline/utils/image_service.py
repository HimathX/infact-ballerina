import requests
from typing import List, Optional, Dict, Any
import logging
import urllib.parse

logger = logging.getLogger(__name__)

class ImageService:
    """Service for fetching images from Unsplash with France24 filtering"""
    
    def __init__(self):
        self.unsplash_access_key = "qpTTv8TGHVVUCBKkLkoA9ybKkVLV9rs_GewlPzsyXKo"
        self.unsplash_base_url = "https://api.unsplash.com"
    
    def is_france24_photo(self, photo: dict) -> bool:
        """Check if photo is from France24"""
        user = photo.get('user', {})
        username = user.get('username', '').lower()
        name = user.get('name', '').lower()
        
        description = photo.get('description', '').lower() if photo.get('description') else ''
        alt_description = photo.get('alt_description', '').lower() if photo.get('alt_description') else ''
        
        france24_indicators = ['france24', 'france 24', 'afp', 'agence france']
        
        for indicator in france24_indicators:
            if (indicator in username or 
                indicator in name or 
                indicator in description or 
                indicator in alt_description):
                return True
        
        return False
    
    def search_images(self, query: str, per_page: int = 4) -> Optional[str]:
        """Search for images and return the first suitable image URL"""
        try:
            headers = {
                "Authorization": f"Client-ID {self.unsplash_access_key}",
                "Accept-Version": "v1"
            }
            
            params = {
                "query": query,
                "per_page": per_page * 2,  # Get more to filter out France24
                "content_filter": "high"
            }
            
            response = requests.get(
                f"{self.unsplash_base_url}/search/photos",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Unsplash API error: {response.status_code}")
                return None
            
            data = response.json()
            all_photos = data.get("results", [])
            
            # Filter out France24 photos and return first suitable one
            for photo in all_photos:
                if not self.is_france24_photo(photo):
                    return photo["urls"]["regular"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching images: {str(e)}")
            return None
    
    def get_cluster_image_url(self, articles: List[Any], cluster_name: str) -> Optional[str]:
        """
        Get image URL for a cluster:
        1. First check if any article has an image_url (excluding France24)
        2. If not found, search Unsplash using cluster keywords
        """
        # Step 1: Check articles for existing image URLs
        for article in articles:
            if hasattr(article, 'image_url') and article.image_url:
                # Check if it's not from France24
                if 'france24' not in article.image_url.lower():
                    return article.image_url
        
        # Step 2: Search Unsplash using cluster name/keywords
        if cluster_name:
            # Clean cluster name for search
            search_query = cluster_name.replace('_', ' ').replace('-', ' ')
            return self.search_images(search_query)
        
        return None