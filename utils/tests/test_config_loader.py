"""
Tests for config_loader module.
"""

import pytest
import os
import yaml
import tempfile
from unittest.mock import patch
from utils.config_loader import Config, get_config


class TestConfig:
    """Test suite for Config class."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            'video': {
                'resolution': [1920, 1080],
                'fps': 30,
                'default_style': 'slideshow'
            },
            'content': {
                'target_segments': 7,
                'segment_duration': 45
            },
            'voiceover': {
                'provider': 'elevenlabs',
                'voice_id': 'test_voice_id',
                'model': 'eleven_monolingual_v1'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_config_initialization(self, temp_config_file):
        """Test Config initialization with valid config file."""
        config = Config(temp_config_file)
        assert config.config is not None
        assert 'video' in config.config
        assert 'content' in config.config
    
    def test_config_missing_file(self):
        """Test Config initialization with missing file uses defaults."""
        config = Config('nonexistent.yaml')
        assert config.config is not None
        assert 'video' in config.config
        assert config.get('video.resolution') == [1920, 1080]
    
    def test_get_nested_value(self, temp_config_file):
        """Test getting nested configuration values."""
        config = Config(temp_config_file)
        assert config.get('video.resolution') == [1920, 1080]
        assert config.get('video.fps') == 30
        assert config.get('content.target_segments') == 7
    
    def test_get_with_default(self, temp_config_file):
        """Test get method with default value."""
        config = Config(temp_config_file)
        assert config.get('nonexistent.key', 'default') == 'default'
        assert config.get('video.nonexistent', 100) == 100
    
    def test_get_invalid_path(self, temp_config_file):
        """Test get method with invalid path."""
        config = Config(temp_config_file)
        assert config.get('invalid.path.to.value') is None
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_openai_key',
        'ELEVENLABS_API_KEY': 'test_elevenlabs_key',
        'UNSPLASH_ACCESS_KEY': 'test_unsplash_key',
        'PEXELS_API_KEY': 'test_pexels_key',
        'VOICE_ID': 'custom_voice_id'
    })
    def test_load_env(self, temp_config_file):
        """Test loading environment variables."""
        config = Config(temp_config_file)
        assert config.openai_api_key == 'test_openai_key'
        assert config.elevenlabs_api_key == 'test_elevenlabs_key'
        assert config.unsplash_access_key == 'test_unsplash_key'
        assert config.pexels_api_key == 'test_pexels_key'
        assert config.config['voiceover']['voice_id'] == 'custom_voice_id'
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key',
        'ELEVENLABS_API_KEY': '',
        'UNSPLASH_ACCESS_KEY': 'test_unsplash',
        'PEXELS_API_KEY': ''
    })
    def test_validate_api_keys(self, temp_config_file):
        """Test API key validation."""
        config = Config(temp_config_file)
        api_status = config.validate_api_keys()
        
        assert api_status['openai'] is True
        assert api_status['elevenlabs'] is False
        assert api_status['unsplash'] is True
        assert api_status['pexels'] is False
    
    def test_ensure_directories(self, temp_config_file):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                'output': {
                    'directory': os.path.join(temp_dir, 'output'),
                    'temp_directory': os.path.join(temp_dir, 'temp')
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config_data, f)
                test_config_path = f.name
            
            config = Config(test_config_path)
            config.ensure_directories()
            
            assert os.path.exists(config.get('output.directory'))
            assert os.path.exists(config.get('output.temp_directory'))
            
            os.unlink(test_config_path)
    
    def test_get_default_config(self):
        """Test default configuration structure."""
        config = Config('nonexistent.yaml')
        default_config = config._get_default_config()
        
        assert 'video' in default_config
        assert 'content' in default_config
        assert 'voiceover' in default_config
        assert 'images' in default_config
        assert 'output' in default_config
        
        assert default_config['video']['resolution'] == [1920, 1080]
        assert default_config['content']['target_segments'] == 7


class TestGetConfig:
    """Test suite for get_config function."""
    
    def test_get_config_singleton(self):
        """Test that get_config returns singleton instance."""
        # Reset singleton
        import utils.config_loader as config_module
        config_module._config_instance = None
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_get_config_with_path(self, tmp_path):
        """Test get_config with custom path."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {'video': {'fps': 60}}
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Reset singleton
        import utils.config_loader as config_module
        config_module._config_instance = None
        
        config = get_config(str(config_file))
        assert config.get('video.fps') == 60


def test_config_yaml_parsing():
    """Test YAML parsing with various data types."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_content = """
video:
  resolution: [1280, 720]
  fps: 24
  enabled: true
content:
  duration: 30.5
"""
        f.write(yaml_content)
        temp_path = f.name
    
    try:
        config = Config(temp_path)
        assert config.get('video.resolution') == [1280, 720]
        assert config.get('video.fps') == 24
        assert config.get('video.enabled') is True
        assert config.get('content.duration') == 30.5
    finally:
        os.unlink(temp_path)

