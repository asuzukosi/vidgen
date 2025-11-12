"""
Pytest configuration and shared fixtures for core module tests.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the project root to sys.path so imports work correctly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_dir():
    """Return the project root directory."""
    return project_root


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF file path for testing."""
    pdf_file = tmp_path / "test_document.pdf"
    return str(pdf_file)


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image file for testing."""
    from PIL import Image
    
    img_file = tmp_path / "test_image.png"
    img = Image.new('RGB', (800, 600), color='red')
    img.save(str(img_file))
    
    return str(img_file)


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Mock API keys in environment."""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_openai_key')
    monkeypatch.setenv('ELEVENLABS_API_KEY', 'test_elevenlabs_key')
    monkeypatch.setenv('UNSPLASH_ACCESS_KEY', 'test_unsplash_key')
    monkeypatch.setenv('PEXELS_API_KEY', 'test_pexels_key')
    monkeypatch.setenv('VOICE_ID', 'test_voice_id')
    
    return {
        'openai': 'test_openai_key',
        'elevenlabs': 'test_elevenlabs_key',
        'unsplash': 'test_unsplash_key',
        'pexels': 'test_pexels_key',
        'voice_id': 'test_voice_id'
    }


@pytest.fixture
def clean_environment(monkeypatch):
    """Remove all API keys from environment."""
    keys_to_remove = [
        'OPENAI_API_KEY',
        'ELEVENLABS_API_KEY',
        'UNSPLASH_ACCESS_KEY',
        'PEXELS_API_KEY',
        'VOICE_ID'
    ]
    
    for key in keys_to_remove:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture(autouse=True)
def reset_logger():
    """Reset logger configuration between tests."""
    import logging
    import core.logger as logger_module
    
    # Reset the configured flag
    logger_module._configured = False
    logger_module._log_dir = None
    
    # Clear all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    yield
    
    # Cleanup after test
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Reset config singleton between tests."""
    import core.config_loader as config_module
    config_module._config_instance = None
    
    yield
    
    config_module._config_instance = None


@pytest.fixture
def sample_video_outline():
    """Create a sample video outline for testing."""
    return {
        'title': 'Test Video Title',
        'total_segments': 3,
        'estimated_duration': 135,
        'segments': [
            {
                'title': 'Introduction',
                'purpose': 'Introduce the main topic',
                'key_points': ['Point 1', 'Point 2', 'Point 3'],
                'visual_keywords': ['intro', 'overview', 'topic'],
                'duration': 45,
                'pdf_images': [],
                'stock_image_query': 'introduction overview',
                'content': 'Introduction content text here.'
            },
            {
                'title': 'Main Content',
                'purpose': 'Explain core concepts',
                'key_points': ['Concept 1', 'Concept 2'],
                'visual_keywords': ['main', 'concept', 'explanation'],
                'duration': 60,
                'pdf_images': [],
                'stock_image_query': 'main concept',
                'content': 'Main content text here.'
            },
            {
                'title': 'Conclusion',
                'purpose': 'Summarize key takeaways',
                'key_points': ['Summary point 1', 'Summary point 2'],
                'visual_keywords': ['conclusion', 'summary', 'takeaway'],
                'duration': 30,
                'pdf_images': [],
                'stock_image_query': 'conclusion summary',
                'content': 'Conclusion content text here.'
            }
        ]
    }


@pytest.fixture
def sample_script_data():
    """Create sample script data for testing."""
    return {
        'title': 'Test Video Title',
        'total_segments': 2,
        'segments': [
            {
                'title': 'Introduction',
                'purpose': 'Introduce the topic',
                'key_points': ['Point 1', 'Point 2'],
                'duration': 45,
                'script': 'This is the introduction script. It introduces the main topic and key concepts.',
                'word_count': 14
            },
            {
                'title': 'Main Content',
                'purpose': 'Explain concepts',
                'key_points': ['Concept 1', 'Concept 2'],
                'duration': 60,
                'script': 'This is the main content script. It explains the core concepts in detail.',
                'word_count': 15
            }
        ],
        'full_script': '[SEGMENT 1: Introduction]\nThis is the introduction script.\n\n[SEGMENT 2: Main Content]\nThis is the main content script.'
    }


@pytest.fixture
def sample_images_metadata():
    """Create sample images metadata for testing."""
    return [
        {
            'filename': 'img_p1_0_hash1.png',
            'filepath': '/tmp/img_p1_0_hash1.png',
            'page_number': 1,
            'width': 800,
            'height': 600,
            'format': 'PNG',
            'mode': 'RGB',
            'size_bytes': 50000,
            'text_context': 'Some context text from the page',
            'label': 'Diagram',
            'description': 'A diagram showing the process',
            'key_elements': ['process', 'flow', 'diagram']
        },
        {
            'filename': 'img_p2_0_hash2.jpg',
            'filepath': '/tmp/img_p2_0_hash2.jpg',
            'page_number': 2,
            'width': 1024,
            'height': 768,
            'format': 'JPEG',
            'mode': 'RGB',
            'size_bytes': 75000,
            'text_context': 'Different context text',
            'label': 'Chart',
            'description': 'A chart displaying data',
            'key_elements': ['chart', 'data', 'visualization']
        }
    ]

