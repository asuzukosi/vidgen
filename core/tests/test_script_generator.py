"""
Tests for script_generator module.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch
from core.script_generator import ScriptGenerator, generate_script


class TestScriptGenerator:
    """Test suite for ScriptGenerator class."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This is a test script for the video segment."))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def generator(self, mock_openai_client, tmp_path):
        """Create a ScriptGenerator instance with mocked client."""
        prompts_dir = tmp_path / 'prompts'
        prompts_dir.mkdir()
        generator = ScriptGenerator('test_api_key', prompts_dir=prompts_dir)
        generator.client = mock_openai_client
        return generator
    
    @pytest.fixture
    def sample_outline(self):
        """Create sample video outline."""
        return {
            'title': 'Test Video',
            'segments': [
                {
                    'title': 'Introduction',
                    'purpose': 'Introduce the topic',
                    'key_points': ['Point 1', 'Point 2'],
                    'duration': 45
                },
                {
                    'title': 'Main Content',
                    'purpose': 'Explain the concept',
                    'key_points': ['Concept 1', 'Concept 2'],
                    'duration': 60
                }
            ]
        }
    
    def test_initialization(self, tmp_path):
        """Test ScriptGenerator initialization."""
        prompts_dir = tmp_path / 'prompts'
        prompts_dir.mkdir()
        generator = ScriptGenerator('test_key', prompts_dir=prompts_dir)
        assert generator.api_key == 'test_key'
        assert generator.model == 'gpt-4o'
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key required"):
                ScriptGenerator()
    
    def test_generate_script(self, generator, sample_outline):
        """Test generating complete script."""
        result = generator.generate_script(sample_outline)
        
        assert 'title' in result
        assert 'segments' in result
        assert 'full_script' in result
        assert len(result['segments']) == 2
        assert all('script' in s for s in result['segments'])
        assert all('word_count' in s for s in result['segments'])
    
    def test_generate_segment_script(self, generator):
        """Test generating script for single segment."""
        segment = {
            'title': 'Test Segment',
            'purpose': 'Test purpose',
            'key_points': ['Point 1', 'Point 2'],
            'duration': 45
        }
        
        script = generator._generate_segment_script(segment, 1, 3, 'Test Video')
        
        assert isinstance(script, str)
        assert len(script) > 0
    
    def test_create_script_prompt(self, generator):
        """Test creating script prompt."""
        segment = {
            'title': 'Test Segment',
            'purpose': 'Test purpose',
            'key_points': ['Point 1', 'Point 2'],
            'duration': 45
        }
        
        prompt = generator._create_script_prompt(segment, 1, 3, 'Test Video')
        
        assert 'Test Video' in prompt
        assert 'Test Segment' in prompt
        assert 'Point 1' in prompt
        assert '45' in prompt
    
    def test_create_script_prompt_intro(self, generator):
        """Test script prompt for introduction segment."""
        segment = {
            'title': 'Introduction',
            'purpose': 'Introduce topic',
            'key_points': [],
            'duration': 30
        }
        
        prompt = generator._create_script_prompt(segment, 1, 5, 'Test Video')
        
        assert 'introduce the topic' in prompt.lower()
    
    def test_create_script_prompt_conclusion(self, generator):
        """Test script prompt for conclusion segment."""
        segment = {
            'title': 'Conclusion',
            'purpose': 'Wrap up',
            'key_points': [],
            'duration': 30
        }
        
        prompt = generator._create_script_prompt(segment, 5, 5, 'Test Video')
        
        assert 'conclusion' in prompt.lower() or 'call-to-action' in prompt.lower()
    
    def test_clean_script(self, generator):
        """Test cleaning script text."""
        raw_script = "[Stage directions] **Bold text** SCRIPT: Narrator: This is the actual script."
        
        cleaned = generator._clean_script(raw_script)
        
        assert '[' not in cleaned
        assert ']' not in cleaned
        assert '**' not in cleaned
        assert 'SCRIPT:' not in cleaned or len(cleaned) > 20
    
    def test_create_fallback_script(self, generator):
        """Test creating fallback script."""
        segment = {
            'title': 'Test Title',
            'purpose': 'Test purpose',
            'key_points': ['Point 1', 'Point 2', 'Point 3']
        }
        
        script = generator._create_fallback_script(segment)
        
        assert 'Test Title' in script
        assert isinstance(script, str)
        assert len(script) > 0
    
    def test_add_transitions(self, generator):
        """Test adding transitions between segments."""
        segments = [
            {'title': 'Segment 1', 'script': 'Script 1'},
            {'title': 'Segment 2', 'script': 'Script 2'},
            {'title': 'Segment 3', 'script': 'Script 3'}
        ]
        
        result = generator._add_transitions(segments)
        
        assert result[0]['transition_to'] == 'Segment 2'
        assert result[1]['transition_to'] == 'Segment 3'
        assert 'transition_to' not in result[2]  # Last segment has no transition
    
    def test_compile_full_script(self, generator):
        """Test compiling full script from segments."""
        segments = [
            {'title': 'Segment 1', 'script': 'This is script one.'},
            {'title': 'Segment 2', 'script': 'This is script two.'}
        ]
        
        full_script = generator._compile_full_script(segments)
        
        assert 'Segment 1' in full_script
        assert 'Segment 2' in full_script
        assert 'This is script one.' in full_script
        assert 'This is script two.' in full_script
    
    def test_save_script(self, generator):
        """Test saving script to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'script.json')
            
            script_data = {
                'title': 'Test',
                'segments': []
            }
            
            generator.save_script(script_data, output_path)
            
            assert os.path.exists(output_path)
    
    def test_export_script_text(self, generator):
        """Test exporting script as text file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'script.txt')
            
            script_data = {
                'title': 'Test Video',
                'full_script': 'This is the full script content.'
            }
            
            generator.export_script_text(script_data, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                content = f.read()
                assert 'Test Video' in content
                assert 'This is the full script content.' in content


class TestGenerateScript:
    """Test suite for generate_script convenience function."""
    
    @patch('core.script_generator.ScriptGenerator')
    def test_generate_script_function(self, mock_generator_class):
        """Test convenience function."""
        mock_generator = MagicMock()
        mock_generator.generate_script.return_value = {'segments': []}
        mock_generator_class.return_value = mock_generator
        
        outline = {'title': 'Test', 'segments': []}
        result = generate_script(outline, 'api_key')
        
        assert 'segments' in result
        mock_generator.generate_script.assert_called_once()

