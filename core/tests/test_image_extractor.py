"""
Tests for image_extractor module.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from core.image_extractor import ImageExtractor, extract_images_from_pdf


class TestImageExtractor:
    """Test suite for ImageExtractor class."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def extractor(self, temp_output_dir):
        """Create an ImageExtractor instance."""
        return ImageExtractor('test.pdf', temp_output_dir)
    
    def test_initialization(self, extractor, temp_output_dir):
        """Test ImageExtractor initialization."""
        assert extractor.pdf_path == 'test.pdf'
        assert extractor.output_dir == temp_output_dir
        assert extractor.images_data == []
        assert os.path.exists(temp_output_dir)
    
    @patch('fitz.open')
    def test_extract_images(self, mock_fitz_open, extractor):
        """Test extracting images from PDF."""
        # Create mock PDF document
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        
        # Mock image on page
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0, 0)]
        
        # Mock image extraction
        mock_pdf.extract_image.return_value = {
            'image': b'fake_image_data',
            'ext': 'png',
            'width': 800,
            'height': 600
        }
        
        mock_pdf.__len__ = lambda self: 1
        mock_pdf.pages = [mock_page]
        mock_fitz_open.return_value = mock_pdf
        
        images = extractor.extract_images(min_width=100, min_height=100)
        
        assert len(images) == 1
        assert images[0]['width'] == 800
        assert images[0]['height'] == 600
        assert images[0]['page_number'] == 1
    
    @patch('fitz.open')
    def test_extract_images_filters_small_images(self, mock_fitz_open, extractor):
        """Test that small images are filtered out."""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0, 0)]
        
        # Small image should be filtered
        mock_pdf.extract_image.return_value = {
            'image': b'fake_image_data',
            'ext': 'png',
            'width': 50,
            'height': 50
        }
        
        mock_pdf.__len__ = lambda self: 1
        mock_pdf.pages = [mock_page]
        mock_fitz_open.return_value = mock_pdf
        
        images = extractor.extract_images(min_width=100, min_height=100)
        
        assert len(images) == 0
    
    def test_extract_text_context(self, extractor):
        """Test extracting text context from page."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is some text context from the page."
        
        context = extractor._extract_text_context(mock_page, None, context_chars=20)
        
        assert context == "This is some text co"
    
    def test_save_metadata(self, extractor):
        """Test saving image metadata to JSON."""
        extractor.images_data = [
            {
                'filename': 'test.png',
                'width': 800,
                'height': 600
            }
        ]
        
        extractor._save_metadata()
        
        metadata_path = os.path.join(extractor.output_dir, 'images_metadata.json')
        assert os.path.exists(metadata_path)
        
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]['filename'] == 'test.png'
    
    def test_load_metadata(self, extractor):
        """Test loading saved metadata."""
        test_data = [
            {
                'filename': 'img1.png',
                'width': 800,
                'height': 600
            }
        ]
        
        metadata_path = os.path.join(extractor.output_dir, 'images_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(test_data, f)
        
        loaded_data = extractor.load_metadata()
        
        assert len(loaded_data) == 1
        assert loaded_data[0]['filename'] == 'img1.png'
    
    def test_load_metadata_file_not_found(self, extractor):
        """Test loading metadata when file doesn't exist."""
        result = extractor.load_metadata()
        assert result == []
    
    def test_get_images_by_page(self, extractor):
        """Test getting images by page number."""
        extractor.images_data = [
            {'page_number': 1, 'filename': 'img1.png'},
            {'page_number': 2, 'filename': 'img2.png'},
            {'page_number': 1, 'filename': 'img3.png'}
        ]
        
        page1_images = extractor.get_images_by_page(1)
        
        assert len(page1_images) == 2
        assert all(img['page_number'] == 1 for img in page1_images)
    
    def test_get_image_stats_empty(self, extractor):
        """Test getting stats with no images."""
        stats = extractor.get_image_stats()
        
        assert stats['total_images'] == 0
        assert stats['average_size'] == 0
        assert stats['formats'] == {}
    
    def test_get_image_stats(self, extractor):
        """Test getting image statistics."""
        extractor.images_data = [
            {
                'size_bytes': 1000,
                'format': 'png',
                'page_number': 1
            },
            {
                'size_bytes': 2000,
                'format': 'jpeg',
                'page_number': 1
            },
            {
                'size_bytes': 1500,
                'format': 'png',
                'page_number': 2
            }
        ]
        
        stats = extractor.get_image_stats()
        
        assert stats['total_images'] == 3
        assert stats['average_size'] == 1500
        assert stats['total_size'] == 4500
        assert stats['formats']['png'] == 2
        assert stats['formats']['jpeg'] == 1
        assert stats['pages_with_images'] == 2


class TestExtractImagesFromPDF:
    """Test suite for extract_images_from_pdf convenience function."""
    
    @patch('fitz.open')
    def test_extract_images_from_pdf_function(self, mock_fitz_open):
        """Test convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            
            mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0, 0)]
            
            mock_pdf.extract_image.return_value = {
                'image': b'fake_image_data',
                'ext': 'png',
                'width': 800,
                'height': 600
            }
            
            mock_pdf.__len__ = lambda self: 1
            mock_pdf.pages = [mock_page]
            mock_fitz_open.return_value = mock_pdf
            
            result = extract_images_from_pdf('test.pdf', temp_dir)
            
            assert isinstance(result, list)

