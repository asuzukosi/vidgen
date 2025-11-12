"""
Tests for content_analyzer module.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch
from core.content_analyzer import ContentAnalyzer, analyze_pdf_content


class TestContentAnalyzer:
    """Test suite for ContentAnalyzer class."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="""
SEGMENT 1: Introduction
PURPOSE: Introduce the main topic
KEY_POINTS:
- Point 1
- Point 2
VISUAL_KEYWORDS: introduction, overview, topic
DURATION: 45

SEGMENT 2: Main Content
PURPOSE: Explain the core concepts
KEY_POINTS:
- Concept 1
- Concept 2
VISUAL_KEYWORDS: concept, diagram, explanation
DURATION: 45
"""))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def analyzer(self, mock_openai_client):
        """Create a ContentAnalyzer instance with mocked client."""
        analyzer = ContentAnalyzer('test_api_key', target_segments=5, segment_duration=45)
        analyzer.client = mock_openai_client
        return analyzer
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content."""
        return {
            'title': 'Test Document',
            'sections': [
                {
                    'title': 'Introduction',
                    'content': 'This is the introduction section with some content.',
                    'level': 1
                },
                {
                    'title': 'Main Section',
                    'content': 'This is the main section with detailed information.',
                    'level': 1
                }
            ],
            'total_pages': 10
        }
    
    def test_initialization(self):
        """Test ContentAnalyzer initialization."""
        analyzer = ContentAnalyzer('test_key', target_segments=7, segment_duration=60)
        assert analyzer.api_key == 'test_key'
        assert analyzer.target_segments == 7
        assert analyzer.segment_duration == 60
        assert analyzer.model == 'gpt-4o'
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key required"):
                ContentAnalyzer()
    
    def test_analyze_content(self, analyzer, sample_pdf_content):
        """Test analyzing PDF content."""
        result = analyzer.analyze_content(sample_pdf_content)
        
        assert 'title' in result
        assert 'segments' in result
        assert 'total_segments' in result
        assert 'estimated_duration' in result
        assert len(result['segments']) >= 2
    
    def test_analyze_content_with_images(self, analyzer, sample_pdf_content):
        """Test analyzing content with images metadata."""
        images_metadata = [
            {
                'label': 'Test Image',
                'description': 'A test image',
                'key_elements': ['element1', 'element2']
            }
        ]
        
        result = analyzer.analyze_content(sample_pdf_content, images_metadata)
        
        assert 'segments' in result
        assert len(result['segments']) >= 2
    
    def test_create_video_outline(self, analyzer, sample_pdf_content):
        """Test creating video outline."""
        outline = analyzer._create_video_outline(sample_pdf_content)
        
        assert 'title' in outline
        assert 'segments' in outline
        assert 'total_segments' in outline
        assert 'estimated_duration' in outline
    
    def test_create_outline_prompt(self, analyzer):
        """Test creating outline prompt."""
        sections = [
            {'title': 'Section 1', 'content_preview': 'Preview 1'},
            {'title': 'Section 2', 'content_preview': 'Preview 2'}
        ]
        
        prompt = analyzer._create_outline_prompt('Test Title', sections, 5, 45)
        
        assert 'Test Title' in prompt
        assert 'Section 1' in prompt
        assert 'Section 2' in prompt
        assert '5' in prompt
        assert '45' in prompt
    
    def test_create_fallback_outline(self, analyzer, sample_pdf_content):
        """Test creating fallback outline."""
        outline = analyzer._create_fallback_outline(sample_pdf_content)
        
        assert 'title' in outline
        assert 'segments' in outline
        assert len(outline['segments']) > 0
        assert any(s['title'] == 'Introduction' for s in outline['segments'])
        assert any(s['title'] == 'Summary' for s in outline['segments'])
    
    def test_extract_key_points(self, analyzer):
        """Test extracting key points from content."""
        content = "First point.\nSecond point.\nThird point.\nFourth point."
        
        points = analyzer._extract_key_points(content, max_points=3)
        
        assert len(points) <= 3
        assert 'First point.' in points
    
    def test_extract_keywords(self, analyzer):
        """Test extracting keywords from text."""
        text = "Introduction to Machine Learning and Data Science"
        
        keywords = analyzer._extract_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
    
    def test_match_images_to_segments(self, analyzer):
        """Test matching images to segments."""
        outline = {
            'segments': [
                {
                    'title': 'Machine Learning',
                    'purpose': 'Explain ML concepts',
                    'visual_keywords': ['machine', 'learning', 'algorithm'],
                    'pdf_images': []
                }
            ]
        }
        
        images_metadata = [
            {
                'label': 'Machine Learning Diagram',
                'description': 'Shows machine learning process',
                'key_elements': ['algorithm', 'data', 'model']
            }
        ]
        
        result = analyzer._match_images_to_segments(outline, images_metadata)
        
        assert len(result['segments'][0]['pdf_images']) > 0
    
    def test_identify_stock_keywords(self, analyzer):
        """Test identifying stock image keywords."""
        outline = {
            'segments': [
                {
                    'title': 'Test Segment',
                    'visual_keywords': ['keyword1', 'keyword2', 'keyword3'],
                    'pdf_images': [],
                    'stock_image_query': None
                }
            ]
        }
        
        result = analyzer._identify_stock_keywords(outline)
        
        assert result['segments'][0]['stock_image_query'] is not None
        assert 'keyword1' in result['segments'][0]['stock_image_query']
    
    def test_identify_stock_keywords_skip_with_images(self, analyzer):
        """Test that segments with enough images don't get stock queries."""
        outline = {
            'segments': [
                {
                    'title': 'Test Segment',
                    'visual_keywords': ['keyword1'],
                    'pdf_images': [{'img': 1}, {'img': 2}],
                    'stock_image_query': None
                }
            ]
        }
        
        result = analyzer._identify_stock_keywords(outline)
        
        # Should not add stock query when already has 2+ images
        assert result['segments'][0]['stock_image_query'] is None
    
    def test_save_outline(self, analyzer):
        """Test saving outline to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'outline.json')
            
            outline = {
                'title': 'Test',
                'segments': []
            }
            
            analyzer.save_outline(outline, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded['title'] == 'Test'


class TestAnalyzePDFContent:
    """Test suite for analyze_pdf_content convenience function."""
    
    @patch('core.content_analyzer.ContentAnalyzer')
    def test_analyze_pdf_content_function(self, mock_analyzer_class):
        """Test convenience function."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_content.return_value = {'segments': []}
        mock_analyzer_class.return_value = mock_analyzer
        
        pdf_content = {'title': 'Test', 'sections': []}
        result = analyze_pdf_content(pdf_content, None, 'api_key')
        
        assert 'segments' in result
        mock_analyzer.analyze_content.assert_called_once()

