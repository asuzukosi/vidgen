"""
Abstract base class for document processors.
Defines the interface that all document processors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class DocumentProcessor(ABC):
    """
    Abstract base class for processing different document types.
    
    All document processors must implement methods to:
    - Extract text content
    - Extract structured content with sections
    - Extract images (if applicable)
    - Provide metadata and statistics
    """
    
    @abstractmethod
    def __enter__(self):
        """Context manager entry. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def extract_text(self) -> str:
        """
        Extract all text from the document.
        
        Returns:
            Complete text content of the document as a string
        """
        pass
    
    @abstractmethod
    def extract_structured_content(self) -> Dict:
        """
        Extract text with structure information (headings, paragraphs, sections).
        
        Returns:
            Dictionary containing structured content with the following structure:
            {
                "title": str,
                "sections": List[Dict],  # Each dict has: title, content, level
                "total_pages": int,  # or equivalent unit
                "metadata": Dict
            }
        """
        pass
    
    @abstractmethod
    def extract_images(self, min_width: int = 100, min_height: int = 100) -> List[Dict]:
        """
        Extract all images from the document.
        
        Args:
            min_width: Minimum image width to extract (filters small icons)
            min_height: Minimum image height to extract
        
        Returns:
            List of dictionaries containing image metadata with structure:
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
        Get statistics about extracted images.
        
        Returns:
            Dictionary with image statistics:
            {
                "total_images": int,
                "average_size": int,
                "total_size": int,
                "formats": Dict[str, int],
                "pages_with_images": int
            }
        """
        pass
    
    def process_all(self, extract_images: bool = True,
                   min_image_width: int = 100,
                   min_image_height: int = 100) -> Dict:
        """
        Process document: extract both text content and images.
        
        Args:
            extract_images: Whether to extract images
            min_image_width: Minimum image width
            min_image_height: Minimum image height
        
        Returns:
            Dictionary containing both structured content and images metadata:
            {
                "content": Dict,  # Result of extract_structured_content()
                "images": List[Dict],  # Result of extract_images()
                "image_stats": Dict  # Result of get_image_stats()
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

