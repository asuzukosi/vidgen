"""
Tests for image_labeler module.
"""

import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from core.image_labeler import ImageLabeler, label_images


class TestImageLabeler:
    """Test suite for ImageLabeler class."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="""
LABEL: Test Image
DESCRIPTION: This is a test image description.
TYPE: diagram
KEY_ELEMENTS: element1, element2, element3
RELEVANCE: high
"""))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def labeler(self, mock_openai_client, tmp_path):
        """Create an ImageLabeler instance with mocked client."""
        prompts_dir = tmp_path / 'prompts'
        prompts_dir.mkdir()
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            labeler = ImageLabeler('test_key', prompts_dir=prompts_dir)
            labeler.client = mock_openai_client
            return labeler
    
    def test_initialization_with_api_key(self, tmp_path):
        """Test ImageLabeler initialization with API key."""
        prompts_dir = tmp_path / 'prompts'
        prompts_dir.mkdir()
        labeler = ImageLabeler('test_api_key', prompts_dir=prompts_dir)
        assert labeler.api_key == 'test_api_key'
        assert labeler.model == 'gpt-4o'
    
    def test_initialization_without_api_key(self):
        """Test ImageLabeler initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                ImageLabeler()
    
    def test_initialization_from_env(self):
        """Test ImageLabeler initialization from environment variable."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env_key'}):
            labeler = ImageLabeler()
            assert labeler.api_key == 'env_key'
    
    @patch('builtins.open', create=True)
    @patch('base64.b64encode')
    def test_label_image(self, mock_b64encode, mock_open, labeler):
        """Test labeling a single image."""
        mock_b64encode.return_value = b'encoded_image_data'
        mock_open.return_value.__enter__.return_value.read.return_value = b'image_data'
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_image = f.name
        
        try:
            result = labeler.label_image(temp_image, "Some text context")
            
            assert 'label' in result
            assert 'description' in result
            assert 'image_type' in result
            assert 'key_elements' in result
            assert result['label'] == 'Test Image'
            assert result['image_type'] == 'diagram'
        finally:
            if os.path.exists(temp_image):
                os.unlink(temp_image)
    
    def test_label_image_error_handling(self, labeler):
        """Test error handling when labeling fails."""
        result = labeler.label_image('nonexistent_image.jpg', "")
        
        assert result['label'] == 'Unlabeled Image'
        assert result['description'] == 'Could not analyze image'
        assert result['image_type'] == 'unknown'
    
    def test_label_images_batch(self, labeler):
        """Test batch labeling of images."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_image = f.name
        
        try:
            images_metadata = [
                {
                    'filepath': temp_image,
                    'text_context': 'Some context',
                    'filename': 'test.jpg'
                }
            ]
            
            with patch('builtins.open', create=True):
                with patch('base64.b64encode', return_value=b'encoded'):
                    result = labeler.label_images_batch(images_metadata)
            
            assert len(result) == 1
            assert 'label' in result[0]
            assert 'description' in result[0]
        finally:
            if os.path.exists(temp_image):
                os.unlink(temp_image)
    
    def test_label_images_batch_skip_labeled(self, labeler):
        """Test that already labeled images are skipped."""
        images_metadata = [
            {
                'filepath': 'test.jpg',
                'label': 'Already Labeled',
                'description': 'Existing description'
            }
        ]
        
        result = labeler.label_images_batch(images_metadata)
        
        assert result[0]['label'] == 'Already Labeled'
        assert result[0]['description'] == 'Existing description'
    
    def test_create_labeling_prompt(self, labeler):
        """Test creating labeling prompt."""
        prompt = labeler._create_labeling_prompt("Sample context text")
        
        assert "LABEL" in prompt
        assert "DESCRIPTION" in prompt
        assert "TYPE" in prompt
        assert "KEY_ELEMENTS" in prompt
        assert "RELEVANCE" in prompt
        assert "Sample context text" in prompt
    
    def test_create_labeling_prompt_no_context(self, labeler):
        """Test creating labeling prompt without context."""
        prompt = labeler._create_labeling_prompt("")
        
        assert "LABEL" in prompt
        assert "DESCRIPTION" in prompt
    
    def test_parse_vision_response(self, labeler):
        """Test parsing vision model response."""
        response_text = """
LABEL: Test Label
DESCRIPTION: Test description here.
TYPE: photo
KEY_ELEMENTS: sky, building, person
RELEVANCE: medium
"""
        result = labeler._parse_vision_response(response_text)
        
        assert result['label'] == 'Test Label'
        assert result['description'] == 'Test description here.'
        assert result['image_type'] == 'photo'
        assert 'sky' in result['key_elements']
        assert result['relevance'] == 'medium'
    
    def test_parse_vision_response_incomplete(self, labeler):
        """Test parsing incomplete vision model response."""
        response_text = "Some random text without proper format"
        
        result = labeler._parse_vision_response(response_text)
        
        assert result['label'] == 'Unlabeled Image'
        assert response_text in result['description']
    
    def test_save_labeled_metadata(self, labeler):
        """Test saving labeled metadata to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'labeled.json')
            
            images_metadata = [
                {
                    'filename': 'test.jpg',
                    'label': 'Test Label',
                    'description': 'Test description'
                }
            ]
            
            labeler.save_labeled_metadata(images_metadata, output_path)
            
            assert os.path.exists(output_path)


class TestLabelImages:
    """Test suite for label_images convenience function."""
    
    @patch('core.image_labeler.ImageLabeler')
    def test_label_images_function(self, mock_labeler_class):
        """Test convenience function."""
        mock_labeler = MagicMock()
        mock_labeler.label_images_batch.return_value = [{'label': 'test'}]
        mock_labeler_class.return_value = mock_labeler
        
        result = label_images([{'filepath': 'test.jpg'}], 'api_key')
        
        assert len(result) == 1
        mock_labeler.label_images_batch.assert_called_once()

