"""
vidgen stock image fetcher module
fetches stock images from unsplash and pexels apis.
"""

import os
import requests
from typing import Optional, List, Dict
from pathlib import Path
import hashlib
from core.logger import get_logger

logger = get_logger(__name__)


class StockImageFetcher:
    """fetch stock images from free apis."""
    
    def __init__(self, unsplash_key: Optional[str] = None, 
                 pexels_key: Optional[str] = None,
                 output_dir: str = "temp/stock_images"):
        """
        initialize stock image fetcher.
        args:
            unsplash_key: unsplash api access key
            pexels_key: pexels api key
            output_dir: directory to save images
        """
        self.unsplash_key = unsplash_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.pexels_key = pexels_key or os.getenv('PEXELS_API_KEY')
        self.output_dir = output_dir
        
        # create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        self.unsplash_base_url = "https://api.unsplash.com"
        self.pexels_base_url = "https://api.pexels.com/v1"
    
    def fetch_image(self, query: str, provider: str = "unsplash") -> Optional[Dict]:
        """
        fetch a single stock image for a query.
        args:
            query: search query
            provider: "unsplash" or "pexels"
        returns:
            image metadata dictionary or None if failed
        """
        if provider == "unsplash" and self.unsplash_key:
            return self._fetch_from_unsplash(query)
        elif provider == "pexels" and self.pexels_key:
            return self._fetch_from_pexels(query)
        else:
            logger.warning(f"{provider} API key not available")
            return None
    
    def _fetch_from_unsplash(self, query: str) -> Optional[Dict]:
        """
        fetch image from unsplash.
        args:
            query: search query
        returns:
            image metadata or None if failed
        """
        try:
            # search for images
            search_url = f"{self.unsplash_base_url}/search/photos"
            headers = {
                "Authorization": f"Client-ID {self.unsplash_key}"
            }
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape"
            }
            
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('results'):
                logger.warning(f"No Unsplash results for query: {query}")
                return None
            
            photo = data['results'][0]
            
            # download image
            image_url = photo['urls']['regular']  # 1080px wide
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # generate filename
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            filename = f"unsplash_{query_hash}_{photo['id']}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            
            # save image
            with open(filepath, 'wb') as f:
                f.write(image_response.content)
            
            logger.info(f"Downloaded Unsplash image for '{query}': {filename}")
            
            # trigger download tracking (unsplash api requirement)
            if photo.get('links', {}).get('download_location'):
                try:
                    requests.get(
                        photo['links']['download_location'],
                        headers=headers
                    )
                except:
                    pass
            
            return {
                'filename': filename,
                'filepath': filepath,
                'source': 'unsplash',
                'query': query,
                'url': photo['urls']['regular'],
                'photographer': photo['user']['name'],
                'photographer_url': photo['user']['links']['html'],
                'photo_url': photo['links']['html'],
                'width': photo['width'],
                'height': photo['height'],
                'description': photo.get('description', ''),
                'alt_description': photo.get('alt_description', '')
            }
            
        except Exception as e:
            logger.error(f"Error fetching from Unsplash: {str(e)}")
            return None
    
    def _fetch_from_pexels(self, query: str) -> Optional[Dict]:
        """
        fetch image from pexels.
        args:
            query: search query
        returns:
            image metadata or None if failed
        """
        try:
            # search for images
            search_url = f"{self.pexels_base_url}/search"
            headers = {
                "Authorization": self.pexels_key
            }
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape"
            }
            
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('photos'):
                logger.warning(f"No Pexels results for query: {query}")
                return None
            
            photo = data['photos'][0]
            
            # download image (use large size)
            image_url = photo['src']['large']  # 940px wide
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            # generate filename
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            filename = f"pexels_{query_hash}_{photo['id']}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            # save image
            with open(filepath, 'wb') as f:
                f.write(image_response.content)
            
            logger.info(f"Downloaded Pexels image for '{query}': {filename}")
            
            return {
                'filename': filename,
                'filepath': filepath,
                'source': 'pexels',
                'query': query,
                'url': photo['src']['large'],
                'photographer': photo['photographer'],
                'photographer_url': photo['photographer_url'],
                'photo_url': photo['url'],
                'width': photo['width'],
                'height': photo['height'],
                'description': photo.get('alt', ''),
                'alt_description': photo.get('alt', '')
            }
            
        except Exception as e:
            logger.error(f"Error fetching from Pexels: {str(e)}")
            return None
    
    def fetch_for_segments(self, segments: List[Dict], preferred_provider: str = "unsplash") -> List[Dict]:
        """
        fetch stock images for video segments.
        args:
            segments: list of segment dictionaries with 'stock_image_query'
            preferred_provider: "unsplash" or "pexels"
        returns:
            updated segments with stock_image metadata
        """
        logger.info(f"fetching stock images for {len(segments)} segments")
        
        for i, segment in enumerate(segments, 1):
            query = segment.get('stock_image_query')
            
            if not query:
                logger.debug(f"Segment {i} has no stock image query")
                continue
            
            # try preferred provider first
            image_data = self.fetch_image(query, preferred_provider)
            
            # fallback to alternative provider
            if not image_data:
                alt_provider = "pexels" if preferred_provider == "unsplash" else "unsplash"
                image_data = self.fetch_image(query, alt_provider)
            
            if image_data:
                segment['stock_image'] = image_data
                logger.info(f"Segment {i} '{segment['title']}': Added stock image")
            else:
                logger.warning(f"Could not fetch stock image for segment {i}")
        
        return segments
    
    def is_available(self) -> Dict[str, bool]:
        """
        check which providers are available.
        returns:
            dictionary of provider availability
        """
        return {
            'unsplash': bool(self.unsplash_key),
            'pexels': bool(self.pexels_key)
        }


def fetch_stock_images(segments: List[Dict], preferred_provider: str = "unsplash") -> List[Dict]:
    """
    convenience function to fetch stock images.
    args:
        segments: video segments
        preferred_provider: preferred image provider
    returns:
        updated segments with stock images
    """
    fetcher = StockImageFetcher()
    return fetcher.fetch_for_segments(segments, preferred_provider)


if __name__ == "__main__":
    # test vidgen stock image fetcher
    import sys
    
    if len(sys.argv) < 2:
        print("usage: python stock_image_fetcher.py <search_query>")
        print("example: python stock_image_fetcher.py 'machine learning'")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    
    print(f"**** testing stock image fetcher ****")
    print(f"query: {query}\n")
    
    fetcher = StockImageFetcher()
    
    # check availability
    availability = fetcher.is_available()
    print("provider availability:")
    for provider, available in availability.items():
        status = "available" if available else "not configured"
        print(f"  {provider.capitalize()}: {status}")
    print()
    
    # try unsplash
    if availability['unsplash']:
        print("**** fetching from unsplash ****")
        image = fetcher.fetch_image(query, "unsplash")
        if image:
            print(f"downloaded: {image['filename']}")
            print(f"photographer: {image['photographer']}")
            print(f"size: {image['width']}x{image['height']}")
            print(f"description: {image.get('alt_description', 'N/A')}")
        print()
    
    # try pexels
    if availability['pexels']:
        print("**** fetching from pexels ****")
        image = fetcher.fetch_image(query, "pexels")
        if image:
            print(f"downloaded: {image['filename']}")
            print(f"photographer: {image['photographer']}")
            print(f"size: {image['width']}x{image['height']}")
        print()
    
    print("**** test complete ****\n")

