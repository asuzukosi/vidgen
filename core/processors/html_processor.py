"""
HTML processor module
Extracts text, structure, and images from HTML documents.
Uses BeautifulSoup for HTML parsing.
"""

import os
import json
import hashlib
import re
import urllib.parse
import io
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from PIL import Image
import requests
from utils.logger import get_logger
from core.processors.document_processor import DocumentProcessor

logger = get_logger(__name__)


class HTMLProcessor(DocumentProcessor):
    """
    Processor for extracting text, structure, and images from HTML documents.
    
    Args:
        html_path: Path to the HTML file or URL
        images_output_dir: Directory to save extracted images (default: "temp/images")
    
    Example:
        with HTMLProcessor('document.html') as processor:
            content = processor.extract_structured_content()
            images = processor.extract_images()
    """
    
    def __init__(self, html_path: str, images_output_dir: str = "temp/images"):
        """
        Initialize HTML processor.
        
        Args:
            html_path: Path to HTML file or URL
            images_output_dir: Directory to save extracted images
        """
        self.html_path = html_path
        self.images_output_dir = images_output_dir
        self.soup = None
        self.html_content = None
        self.images_data = []
        self.is_url = html_path.startswith(('http://', 'https://'))
        
        # Create output directory for images
        Path(images_output_dir).mkdir(parents=True, exist_ok=True)
        
    def __enter__(self):
        """Context manager entry."""
        if self.is_url:
            response = requests.get(self.html_path)
            response.raise_for_status()
            self.html_content = response.text
        else:
            if not os.path.exists(self.html_path):
                raise FileNotFoundError(f"HTML file not found: {self.html_path}")
            with open(self.html_path, 'r', encoding='utf-8') as f:
                self.html_content = f.read()
        
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.soup = None
        self.html_content = None
    
    def extract_text(self) -> str:
        """
        Extract all text from the HTML document.
        
        Returns:
            Complete text content of the HTML document
        """
        if not self.soup:
            raise ValueError("HTML document not opened. Use context manager or call __enter__()")
        
        # Remove script and style elements
        for script in self.soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = self.soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info("Extracted text from HTML document")
        return text
    
    def extract_structured_content(self) -> Dict:
        """
        Extract text with structure information (headings, paragraphs, sections).
        
        Returns:
            Dictionary containing structured content
        """
        if not self.soup:
            raise ValueError("HTML document not opened. Use context manager or call __enter__()")
        
        # Extract title
        title = self._extract_title()
        
        # Extract sections based on headings
        sections = self._extract_sections()
        
        # Count "pages" (approximate by major sections)
        total_sections = len([s for s in sections if s['level'] == 1])
        
        structured_content = {
            "title": title,
            "sections": sections,
            "total_pages": max(total_sections, 1),  # At least 1 page
            "metadata": {
                "source": self.html_path,
                "is_url": self.is_url
            }
        }
        
        return structured_content
    
    def _extract_title(self) -> str:
        """
        Extract document title from HTML.
        
        Returns:
            Document title
        """
        # Try <title> tag first
        title_tag = self.soup.find('title')
        if title_tag and title_tag.get_text().strip():
            return title_tag.get_text().strip()
        
        # Try <h1> tag
        h1_tag = self.soup.find('h1')
        if h1_tag and h1_tag.get_text().strip():
            return h1_tag.get_text().strip()
        
        # Try meta title
        meta_title = self.soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title.get('content').strip()
        
        return "untitled document"
    
    def _extract_sections(self) -> List[Dict]:
        """
        Extract sections from HTML based on heading tags.
        
        Returns:
            List of sections with title and content
        """
        sections = []
        current_section = None
        
        # Find all heading and content elements
        elements = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div'])
        
        for element in elements:
            tag_name = element.name
            
            # Check if it's a heading
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Save previous section if it exists
                if current_section and current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                level = int(tag_name[1])  # h1 -> 1, h2 -> 2, etc.
                title = element.get_text().strip()
                current_section = {
                    "title": title if title else "untitled section",
                    "content": "",
                    "level": level
                }
            elif current_section and tag_name in ['p', 'div']:
                # Add content to current section
                text = element.get_text().strip()
                if text:
                    current_section["content"] += text + "\n\n"
        
        # Add the last section
        if current_section and current_section['content'].strip():
            sections.append(current_section)
        
        # If no sections found, create one with all content
        if not sections:
            text = self.extract_text()
            sections.append({
                "title": "content",
                "content": text,
                "level": 1
            })
        
        logger.info(f"Identified {len(sections)} sections")
        return sections
    
    def extract_images(self, min_width: int = 100, min_height: int = 100) -> List[Dict]:
        """
        Extract all images from the HTML document.
        
        Args:
            min_width: Minimum image width to extract
            min_height: Minimum image height to extract
        
        Returns:
            List of dictionaries containing image metadata
        """
        if not self.soup:
            raise ValueError("HTML document not opened. Use context manager or call __enter__()")
        
        logger.info(f"Starting image extraction from {self.html_path}")
        
        image_count = 0
        img_tags = self.soup.find_all('img')
        
        for img_index, img_tag in enumerate(img_tags):
            try:
                # Get image source
                src = img_tag.get('src') or img_tag.get('data-src') or ''
                if not src:
                    continue
                
                # Resolve relative URLs
                if self.is_url:
                    img_url = urllib.parse.urljoin(self.html_path, src)
                else:
                    # For local files, resolve relative paths
                    if not os.path.isabs(src):
                        base_dir = os.path.dirname(self.html_path)
                        img_url = os.path.join(base_dir, src)
                        img_url = os.path.normpath(img_url)
                    else:
                        img_url = src
                
                # Download or read image
                try:
                    if self.is_url or img_url.startswith('http'):
                        response = requests.get(img_url, timeout=10)
                        response.raise_for_status()
                        image_bytes = response.content
                    else:
                        if not os.path.exists(img_url):
                            logger.warning(f"Image file not found: {img_url}")
                            continue
                        with open(img_url, 'rb') as f:
                            image_bytes = f.read()
                except Exception as e:
                    logger.warning(f"Could not load image {img_url}: {str(e)}")
                    continue
                
                # Get image dimensions
                try:
                    with Image.open(io.BytesIO(image_bytes)) as pil_img:
                        width, height = pil_img.size
                        format_name = pil_img.format
                        mode = pil_img.mode
                except Exception as e:
                    logger.warning(f"Could not read image metadata: {str(e)}")
                    continue
                
                # Filter by size
                if width < min_width or height < min_height:
                    logger.debug(f"Skipping small image: {width}x{height}")
                    continue
                
                # Generate unique filename
                image_hash = hashlib.md5(image_bytes).hexdigest()[:10]
                ext = format_name.lower() if format_name else 'jpg'
                filename = f"img_html_{img_index}_{image_hash}.{ext}"
                filepath = os.path.join(self.images_output_dir, filename)
                
                # Save image
                with open(filepath, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # Get alt text and surrounding context
                alt_text = img_tag.get('alt', '')
                text_context = self._extract_text_context(img_tag)
                
                # Store metadata
                image_metadata = {
                    "filename": filename,
                    "filepath": filepath,
                    "page_number": 1,  # HTML doesn't have pages, use 1
                    "width": width,
                    "height": height,
                    "format": format_name or "unknown",
                    "mode": mode,
                    "size_bytes": len(image_bytes),
                    "text_context": text_context,
                    "alt_text": alt_text,
                    "source_url": img_url,
                    "label": None,
                    "description": None,
                    "relevance_score": None
                }
                
                self.images_data.append(image_metadata)
                image_count += 1
                
                logger.info(f"Extracted image {image_count}: {filename} ({width}x{height})")
                
            except Exception as e:
                logger.error(f"Error extracting image {img_index}: {str(e)}")
                continue
        
        logger.info(f"Extracted {image_count} images from HTML document")
        
        # Save metadata
        self._save_image_metadata()
        
        return self.images_data
    
    def _extract_text_context(self, img_tag, context_chars: int = 500) -> str:
        """
        Extract text near an image in the HTML.
        
        Args:
            img_tag: BeautifulSoup image tag
            context_chars: Number of characters to extract
        
        Returns:
            Text context surrounding the image
        """
        try:
            # Get parent element and extract text
            parent = img_tag.find_parent(['article', 'section', 'div', 'p'])
            if parent:
                text = parent.get_text().strip()
                if len(text) > context_chars:
                    return text[:context_chars]
                return text
            return img_tag.get('alt', '')
        except Exception as e:
            logger.debug(f"Could not extract text context: {str(e)}")
            return ""
    
    def _save_image_metadata(self):
        """Save image metadata to JSON file."""
        metadata_path = os.path.join(self.images_output_dir, "images_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(self.images_data, f, indent=2)
        
        logger.info(f"Saved metadata to {metadata_path}")
    
    def get_image_stats(self) -> Dict:
        """
        Get statistics about extracted images.
        
        Returns:
            Dictionary with image statistics
        """
        if not self.images_data:
            return {
                "total_images": 0,
                "average_size": 0,
                "formats": {},
                "pages_with_images": 0
            }
        
        total_size = sum(img['size_bytes'] for img in self.images_data)
        formats = {}
        for img in self.images_data:
            fmt = img.get('format', 'unknown')
            formats[fmt] = formats.get(fmt, 0) + 1
        
        return {
            "total_images": len(self.images_data),
            "average_size": total_size // len(self.images_data) if self.images_data else 0,
            "total_size": total_size,
            "formats": formats,
            "pages_with_images": 1 if self.images_data else 0  # HTML is single "page"
        }

