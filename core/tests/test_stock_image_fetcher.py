"""
Tests for stock_image_fetcher module.
"""

import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from core.stock_image_fetcher import StockImageFetcher, fetch_stock_images


class TestStockImageFetcher:
    """Test suite for StockImageFetcher class."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def fetcher(self, temp_output_dir):
        """Create a StockImageFetcher instance."""
        return StockImageFetcher(
            unsplash_key='test_unsplash_key',
            pexels_key='test_pexels_key',
            output_dir=temp_output_dir
        )
    
    def test_initialization(self, fetcher, temp_output_dir):
        """Test StockImageFetcher initialization."""
        assert fetcher.unsplash_key == 'test_unsplash_key'
        assert fetcher.pexels_key == 'test_pexels_key'
        assert fetcher.output_dir == temp_output_dir
        assert os.path.exists(temp_output_dir)
    
    def test_initialization_from_env(self):
        """Test initialization from environment variables."""
        with patch.dict(os.environ, {
            'UNSPLASH_ACCESS_KEY': 'env_unsplash',
            'PEXELS_API_KEY': 'env_pexels'
        }):
            fetcher = StockImageFetcher()
            assert fetcher.unsplash_key == 'env_unsplash'
            assert fetcher.pexels_key == 'env_pexels'
    
    @patch('requests.get')
    def test_fetch_from_unsplash(self, mock_get, fetcher):
        """Test fetching image from Unsplash."""
        # Mock search response
        search_response = MagicMock()
        search_response.json.return_value = {
            'results': [{
                'id': 'test123',
                'urls': {'regular': 'https://example.com/image.jpg'},
                'user': {
                    'name': 'Test Photographer',
                    'links': {'html': 'https://unsplash.com/@photographer'}
                },
                'links': {
                    'html': 'https://unsplash.com/photos/test123',
                    'download_location': 'https://api.unsplash.com/download/test123'
                },
                'width': 1920,
                'height': 1080,
                'description': 'Test image',
                'alt_description': 'Test alt'
            }]
        }
        
        # Mock image download response
        image_response = MagicMock()
        image_response.content = b'fake_image_data'
        
        # Configure mock to return different responses
        mock_get.side_effect = [search_response, image_response, MagicMock()]
        
        result = fetcher._fetch_from_unsplash('test query')
        
        assert result is not None
        assert result['source'] == 'unsplash'
        assert result['photographer'] == 'Test Photographer'
        assert result['width'] == 1920
        assert result['height'] == 1080
    
    @patch('requests.get')
    def test_fetch_from_unsplash_no_results(self, mock_get, fetcher):
        """Test fetching from Unsplash with no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': []}
        mock_get.return_value = mock_response
        
        result = fetcher._fetch_from_unsplash('nonexistent query')
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_from_pexels(self, mock_get, fetcher):
        """Test fetching image from Pexels."""
        # Mock search response
        search_response = MagicMock()
        search_response.json.return_value = {
            'photos': [{
                'id': 456,
                'src': {'large': 'https://example.com/pexels.jpg'},
                'photographer': 'Test Photographer',
                'photographer_url': 'https://pexels.com/@photographer',
                'url': 'https://pexels.com/photo/456',
                'width': 1920,
                'height': 1080,
                'alt': 'Test image'
            }]
        }
        
        # Mock image download response
        image_response = MagicMock()
        image_response.content = b'fake_image_data'
        
        mock_get.side_effect = [search_response, image_response]
        
        result = fetcher._fetch_from_pexels('test query')
        
        assert result is not None
        assert result['source'] == 'pexels'
        assert result['photographer'] == 'Test Photographer'
        assert result['width'] == 1920
    
    @patch('requests.get')
    def test_fetch_from_pexels_no_results(self, mock_get, fetcher):
        """Test fetching from Pexels with no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'photos': []}
        mock_get.return_value = mock_response
        
        result = fetcher._fetch_from_pexels('nonexistent query')
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_image_unsplash(self, mock_get, fetcher):
        """Test fetch_image with Unsplash provider."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{
                'id': 'test',
                'urls': {'regular': 'https://example.com/image.jpg'},
                'user': {'name': 'Test', 'links': {'html': 'https://test.com'}},
                'links': {'html': 'https://test.com', 'download_location': 'https://test.com'},
                'width': 800,
                'height': 600,
                'description': 'Test',
                'alt_description': 'Test'
            }]
        }
        
        mock_image = MagicMock()
        mock_image.content = b'image_data'
        
        mock_get.side_effect = [mock_response, mock_image, MagicMock()]
        
        result = fetcher.fetch_image('test', 'unsplash')
        
        assert result is not None
        assert result['source'] == 'unsplash'
    
    def test_fetch_image_no_api_key(self, temp_output_dir):
        """Test fetch_image without API keys."""
        fetcher = StockImageFetcher(
            unsplash_key=None,
            pexels_key=None,
            output_dir=temp_output_dir
        )
        
        result = fetcher.fetch_image('test', 'unsplash')
        
        assert result is None
    
    @patch('core.stock_image_fetcher.StockImageFetcher.fetch_image')
    def test_fetch_for_segments(self, mock_fetch, fetcher):
        """Test fetching images for video segments."""
        mock_fetch.return_value = {
            'filename': 'test.jpg',
            'source': 'unsplash'
        }
        
        segments = [
            {
                'title': 'Segment 1',
                'stock_image_query': 'query1'
            },
            {
                'title': 'Segment 2',
                'stock_image_query': 'query2'
            },
            {
                'title': 'Segment 3',
                'stock_image_query': None
            }
        ]
        
        result = fetcher.fetch_for_segments(segments, 'unsplash')
        
        assert 'stock_image' in result[0]
        assert 'stock_image' in result[1]
        assert 'stock_image' not in result[2]
    
    @patch('core.stock_image_fetcher.StockImageFetcher.fetch_image')
    def test_fetch_for_segments_with_fallback(self, mock_fetch, fetcher):
        """Test fetching with fallback to alternative provider."""
        # First call returns None (Unsplash fails), second returns image (Pexels succeeds)
        mock_fetch.side_effect = [
            None,
            {'filename': 'test.jpg', 'source': 'pexels'}
        ]
        
        segments = [
            {
                'title': 'Segment 1',
                'stock_image_query': 'query1'
            }
        ]
        
        result = fetcher.fetch_for_segments(segments, 'unsplash')
        
        assert 'stock_image' in result[0]
        assert result[0]['stock_image']['source'] == 'pexels'
    
    def test_is_available(self, fetcher):
        """Test checking provider availability."""
        availability = fetcher.is_available()
        
        assert 'unsplash' in availability
        assert 'pexels' in availability
        assert availability['unsplash'] is True
        assert availability['pexels'] is True
    
    def test_is_available_no_keys(self, temp_output_dir):
        """Test availability check with no API keys."""
        fetcher = StockImageFetcher(
            unsplash_key=None,
            pexels_key=None,
            output_dir=temp_output_dir
        )
        
        availability = fetcher.is_available()
        
        assert availability['unsplash'] is False
        assert availability['pexels'] is False
    
    @patch('requests.get')
    def test_fetch_from_unsplash_error_handling(self, mock_get, fetcher):
        """Test error handling in Unsplash fetching."""
        mock_get.side_effect = Exception("Network error")
        
        result = fetcher._fetch_from_unsplash('test')
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_from_pexels_error_handling(self, mock_get, fetcher):
        """Test error handling in Pexels fetching."""
        mock_get.side_effect = Exception("Network error")
        
        result = fetcher._fetch_from_pexels('test')
        
        assert result is None


class TestFetchStockImages:
    """Test suite for fetch_stock_images convenience function."""
    
    @patch('core.stock_image_fetcher.StockImageFetcher')
    def test_fetch_stock_images_function(self, mock_fetcher_class):
        """Test convenience function."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_for_segments.return_value = [{'stock_image': {}}]
        mock_fetcher_class.return_value = mock_fetcher
        
        segments = [{'stock_image_query': 'test'}]
        result = fetch_stock_images(segments, 'unsplash')
        
        assert len(result) == 1
        mock_fetcher.fetch_for_segments.assert_called_once()

