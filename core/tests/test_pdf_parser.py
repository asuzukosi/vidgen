"""
Tests for pdf_parser module.
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from core.pdf_parser import PDFParser, parse_pdf


class TestPDFParser:
    """Test suite for PDFParser class."""
    
    @pytest.fixture
    def mock_pdf(self):
        """Create a mock PDF object."""
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        
        # Create mock pages
        for i in range(3):
            page = MagicMock()
            page.extract_text.return_value = f"Page {i+1} content with some text."
            mock_pdf.pages.append(page)
        
        mock_pdf.metadata = {'Title': 'Test Document'}
        return mock_pdf
    
    @pytest.fixture
    def parser(self):
        """Create a PDFParser instance."""
        return PDFParser('test.pdf')
    
    def test_initialization(self, parser):
        """Test PDFParser initialization."""
        assert parser.pdf_path == 'test.pdf'
        assert parser.pdf is None
        assert parser.pages_data == []
    
    @patch('pdfplumber.open')
    def test_context_manager_enter(self, mock_open, parser, mock_pdf):
        """Test context manager __enter__."""
        mock_open.return_value = mock_pdf
        
        with parser as p:
            assert p.pdf is not None
            assert p.pdf == mock_pdf
    
    @patch('pdfplumber.open')
    def test_context_manager_exit(self, mock_open, parser, mock_pdf):
        """Test context manager __exit__."""
        mock_open.return_value = mock_pdf
        
        with parser:
            pass
        
        mock_pdf.close.assert_called_once()
    
    @patch('pdfplumber.open')
    def test_extract_text(self, mock_open, parser, mock_pdf):
        """Test extracting text from PDF."""
        mock_open.return_value = mock_pdf
        
        with parser:
            text = parser.extract_text()
        
        assert "Page 1 content" in text
        assert "Page 2 content" in text
        assert "Page 3 content" in text
    
    @patch('pdfplumber.open')
    def test_extract_text_without_opening(self, mock_open, parser):
        """Test extract_text raises error when PDF not opened."""
        with pytest.raises(ValueError, match="pdf document not opened"):
            parser.extract_text()
    
    @patch('pdfplumber.open')
    def test_get_page_count(self, mock_open, parser, mock_pdf):
        """Test getting page count."""
        mock_open.return_value = mock_pdf
        
        with parser:
            count = parser.get_page_count()
        
        assert count == 3
    
    @patch('pdfplumber.open')
    def test_extract_structured_content(self, mock_open, parser, mock_pdf):
        """Test extracting structured content."""
        mock_open.return_value = mock_pdf
        
        with parser:
            content = parser.extract_structured_content()
        
        assert 'title' in content
        assert 'sections' in content
        assert 'total_pages' in content
        assert 'metadata' in content
        assert content['total_pages'] == 3
    
    @patch('pdfplumber.open')
    def test_extract_title_from_metadata(self, mock_open, parser):
        """Test extracting title from metadata."""
        mock_pdf = MagicMock()
        mock_pdf.metadata = {'Title': 'Document Title'}
        mock_pdf.pages = [MagicMock()]
        mock_open.return_value = mock_pdf
        
        with parser:
            title = parser._extract_title()
        
        assert title == 'Document Title'
    
    @patch('pdfplumber.open')
    def test_extract_title_from_first_page(self, mock_open, parser):
        """Test extracting title from first page when metadata unavailable."""
        mock_pdf = MagicMock()
        mock_pdf.metadata = {}
        
        first_page = MagicMock()
        first_page.extract_text.return_value = "Short line\nThis is a proper title line\nMore content"
        mock_pdf.pages = [first_page]
        mock_open.return_value = mock_pdf
        
        with parser:
            title = parser._extract_title()
        
        assert title == "This is a proper title line"
    
    def test_is_likely_heading(self, parser):
        """Test heading detection."""
        assert parser._is_likely_heading("1. Introduction") is True
        assert parser._is_likely_heading("Chapter 1") is True
        assert parser._is_likely_heading("Section 2.1") is True
        assert parser._is_likely_heading("HEADING IN CAPS") is True
        assert parser._is_likely_heading("1.1 Subsection") is True
        
        # Should not be headings
        assert parser._is_likely_heading("a" * 300) is False  # Too long
        assert parser._is_likely_heading("ab") is False  # Too short
        assert parser._is_likely_heading("This is a regular paragraph with normal text.") is False
    
    def test_detect_heading_level(self, parser):
        """Test heading level detection."""
        assert parser._detect_heading_level("1. Introduction") == 1
        assert parser._detect_heading_level("1.1 Subsection") == 2
        assert parser._detect_heading_level("1.1.1 Sub-subsection") == 3
        assert parser._detect_heading_level("MAIN HEADING") == 1
        assert parser._detect_heading_level("Subheading") == 2
    
    @patch('pdfplumber.open')
    def test_identify_sections(self, mock_open, parser):
        """Test section identification."""
        text = """1. Introduction
This is the introduction paragraph.

2. Background
This is the background section.

Regular paragraph without heading."""
        
        mock_pdf = MagicMock()
        mock_open.return_value = mock_pdf
        
        with parser:
            sections = parser._identify_sections(text)
        
        assert len(sections) > 0
        assert any('Introduction' in s['title'] or 'introduction' in s['title'] 
                  for s in sections)
    
    @patch('pdfplumber.open')
    def test_extract_text_by_page(self, mock_open, parser, mock_pdf):
        """Test extracting text by page."""
        mock_open.return_value = mock_pdf
        
        with parser:
            pages_text = parser.extract_text_by_page()
        
        assert len(pages_text) == 3
        assert "Page 1" in pages_text[0]
        assert "Page 2" in pages_text[1]
        assert "Page 3" in pages_text[2]


class TestParsePDF:
    """Test suite for parse_pdf convenience function."""
    
    @patch('pdfplumber.open')
    def test_parse_pdf_function(self, mock_open):
        """Test parse_pdf convenience function."""
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = "Test content"
        mock_pdf.metadata = {'Title': 'Test'}
        mock_open.return_value = mock_pdf
        
        result = parse_pdf('test.pdf')
        
        assert 'title' in result
        assert 'sections' in result
        assert 'total_pages' in result


def test_pdf_parser_empty_pages():
    """Test handling of empty pages."""
    with patch('pdfplumber.open') as mock_open:
        mock_pdf = MagicMock()
        
        # Create pages with None text
        page1 = MagicMock()
        page1.extract_text.return_value = None
        page2 = MagicMock()
        page2.extract_text.return_value = "Page 2 content"
        
        mock_pdf.pages = [page1, page2]
        mock_pdf.metadata = {}
        mock_open.return_value = mock_pdf
        
        parser = PDFParser('test.pdf')
        with parser:
            text = parser.extract_text()
        
        # Should handle None gracefully
        assert text is not None
        assert "Page 2 content" in text

