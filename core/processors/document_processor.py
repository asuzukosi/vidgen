"""
abstract base class for the input document processors.
"""

from abc import ABC, abstractmethod
from typing import Dict, List


class DocumentProcessor(ABC):
    """
    abstract base class for the input document processors.
    all document processors must implement methods to:
    - extract text content
    - extract structured content with sections
    - extract images (if applicable)
    - provide metadata and statistics
    """
    
    # ==================== CONTEXT MANAGER METHODS ====================
    @abstractmethod
    def __enter__(self):
        """context manager entry. must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """context manager exit. must be implemented by subclasses."""
        pass
    
    # ==================== TEXT EXTRACTION METHODS ====================
    @abstractmethod
    def extract_text(self) -> str:
        """
        extract all text from the document.
        returns:
            complete text content of the document as a string
        """
        pass
    
    @abstractmethod
    def extract_structured_content(self) -> Dict:
        """
        extract text with structure information (headings, paragraphs, sections).
        returns:
            dictionary containing structured content with the following structure:
            {
                "title": str,
                "sections": List[Dict],  # Each dict has: title, content, level
                "total_pages": int,  # or equivalent unit
                "metadata": Dict
            }
        """
        pass
    
    # ==================== IMAGE EXTRACTION METHODS ====================
    @abstractmethod
    def extract_images(self, min_width: int = 100, min_height: int = 100) -> List[Dict]:
        """
        extract all images from the document.
        returns:
            list of dictionaries containing image metadata with structure:
            {
                "filename": str,
                "filepath": str,
                "page_number": int,  # or section number
                "width": int,
                "height": int,
                "format": str,
                "mode": str,
                "size_bytes": int,
                "text_context": str,
                "label": Optional[str],
                "description": Optional[str],
                "relevance_score": Optional[float]
            }
        """
        pass
    
    @abstractmethod
    def get_image_stats(self) -> Dict:
        """
        get statistics about extracted images.
        returns:
            dictionary with image statistics:
            {
                "total_images": int,
                "average_size": int,
                "total_size": int,
                "formats": Dict[str, int],
                "pages_with_images": int
            }
        """
        pass
    
    # ==================== PROCESS ALL METHOD ====================
    def process_all(self, extract_images: bool = True,
                   min_image_width: int = 100,
                   min_image_height: int = 100) -> Dict:
        """
        process document: extract both text content and images.
        args:
            extract_images: whether to extract images
            min_image_width: minimum image width
            min_image_height: minimum image height
        returns:
            dictionary containing both structured content and images metadata with the following structure:
            {
                "content": Dict,
                "images": List[Dict],
                "image_stats": Dict
            }
        """
        content = self.extract_structured_content()
        images = []
        
        if extract_images:
            images = self.extract_images(min_image_width, min_image_height)
        
        return {
            "content": content,
            "images": images,
            "image_stats": self.get_image_stats() if images else {}
        }

