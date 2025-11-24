"""
Tests for video_utils module.
"""

import numpy as np
import tempfile
import os
from unittest.mock import MagicMock, patch
from PIL import Image
from utils.video_utils import VideoUtils


class TestVideoUtils:
    """Test suite for VideoUtils class."""
    
    def test_create_gradient_background(self):
        """Test creating gradient background."""
        gradient = VideoUtils.create_gradient_background(
            1920, 1080,
            color1=(30, 60, 114),
            color2=(42, 82, 152)
        )
        
        assert gradient.shape == (1080, 1920, 3)
        assert gradient.dtype == np.uint8
        # Check that top and bottom are different colors (gradient)
        assert not np.array_equal(gradient[0, 0], gradient[-1, 0])
    
    def test_create_solid_background(self):
        """Test creating solid color background."""
        background = VideoUtils.create_solid_background(
            1920, 1080,
            color=(255, 0, 0)
        )
        
        assert background.shape == (1080, 1920, 3)
        assert background.dtype == np.uint8
        # Check that all pixels are the same color
        assert np.all(background == [255, 0, 0])
    
    def test_resize_image_to_fit(self):
        """Test resizing image to fit dimensions."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            # Create a test image
            img = Image.new('RGB', (2000, 1000), color='red')
            img.save(f.name)
            temp_image = f.name
        
        try:
            resized = VideoUtils.resize_image_to_fit(temp_image, 1000, 500)
            
            # Should maintain aspect ratio and fit within 1000x500
            assert resized.width <= 1000
            assert resized.height <= 500
        finally:
            if os.path.exists(temp_image):
                os.unlink(temp_image)
    
    def test_resize_image_to_fit_no_aspect(self):
        """Test resizing image without maintaining aspect ratio."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (2000, 1000), color='blue')
            img.save(f.name)
            temp_image = f.name
        
        try:
            resized = VideoUtils.resize_image_to_fit(
                temp_image, 500, 500, maintain_aspect=False
            )
            
            assert resized.width == 500
            assert resized.height == 500
        finally:
            if os.path.exists(temp_image):
                os.unlink(temp_image)
    
    def test_add_text_to_image(self):
        """Test adding text to image."""
        img = Image.new('RGB', (800, 600), color='white')
        
        result = VideoUtils.add_text_to_image(
            img, "Test Text",
            position=(100, 100),
            font_size=40,
            color=(0, 0, 0)
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == (800, 600)
        # Image should be different after adding text
        assert not np.array_equal(np.array(img), np.array(result))
    
    def test_add_text_to_image_with_max_width(self):
        """Test adding text with max width (wrapping)."""
        img = Image.new('RGB', (800, 600), color='white')
        
        long_text = "This is a very long text that should wrap to multiple lines"
        
        result = VideoUtils.add_text_to_image(
            img, long_text,
            position=(50, 50),
            font_size=30,
            color=(0, 0, 0),
            max_width=400
        )
        
        assert isinstance(result, Image.Image)
    
    def test_wrap_text(self):
        """Test text wrapping."""
        from PIL import ImageDraw, ImageFont
        
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            font = ImageFont.load_default()
        
        text = "This is a long sentence that should be wrapped into multiple lines"
        wrapped = VideoUtils._wrap_text(text, font, 200, draw)
        
        # Should have multiple lines
        assert '\n' in wrapped or len(wrapped) < len(text)
    
    def test_create_title_card(self):
        """Test creating title card."""
        title_card = VideoUtils.create_title_card(
            1920, 1080,
            "Test Title",
            "Test Subtitle"
        )
        
        assert title_card.shape == (1080, 1920, 3)
        assert title_card.dtype == np.uint8
    
    def test_create_title_card_no_subtitle(self):
        """Test creating title card without subtitle."""
        title_card = VideoUtils.create_title_card(
            1920, 1080,
            "Test Title"
        )
        
        assert title_card.shape == (1080, 1920, 3)
        assert title_card.dtype == np.uint8
    
    def test_create_end_card(self):
        """Test creating end card."""
        end_card = VideoUtils.create_end_card(
            1920, 1080,
            "Thank you!",
            ["Credit 1", "Credit 2"]
        )
        
        assert end_card.shape == (1080, 1920, 3)
        assert end_card.dtype == np.uint8
    
    def test_create_end_card_no_credits(self):
        """Test creating end card without credits."""
        end_card = VideoUtils.create_end_card(
            1920, 1080,
            "Thank you!"
        )
        
        assert end_card.shape == (1080, 1920, 3)
        assert end_card.dtype == np.uint8
    
    @patch('moviepy.video.fx.fadein')
    @patch('moviepy.video.fx.fadeout')
    def test_add_fade_transition(self, mock_fadeout, mock_fadein):
        """Test adding fade transition to clip."""
        mock_clip = MagicMock()
        mock_clip.fx.return_value = mock_clip
        
        result = VideoUtils.add_fade_transition(mock_clip, fade_duration=1.0)
        
        # Should call fx twice (fadein and fadeout)
        assert mock_clip.fx.call_count == 2
    
    def test_composite_image_on_background(self):
        """Test compositing image on background."""
        background = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (400, 300), color='red')
            img.save(f.name)
            temp_image = f.name
        
        try:
            result = VideoUtils.composite_image_on_background(
                background, temp_image,
                position='center',
                scale=0.5
            )
            
            assert result.shape == background.shape
            # Should have some non-zero pixels (the composited image)
            assert np.any(result > 0)
        finally:
            if os.path.exists(temp_image):
                os.unlink(temp_image)
    
    def test_composite_image_different_positions(self):
        """Test compositing at different positions."""
        background = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (200, 150), color='blue')
            img.save(f.name)
            temp_image = f.name
        
        try:
            positions = ['center', 'left', 'right', 'top', 'bottom']
            
            for pos in positions:
                result = VideoUtils.composite_image_on_background(
                    background.copy(), temp_image,
                    position=pos,
                    scale=0.3
                )
                
                assert result.shape == background.shape
                assert np.any(result > 0)
        finally:
            if os.path.exists(temp_image):
                os.unlink(temp_image)
    
    def test_composite_image_rgba(self):
        """Test compositing RGBA image."""
        background = np.zeros((600, 800, 3), dtype=np.uint8)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGBA', (200, 150), color=(255, 0, 0, 128))
            img.save(f.name)
            temp_image = f.name
        
        try:
            result = VideoUtils.composite_image_on_background(
                background, temp_image,
                position='center',
                scale=0.5
            )
            
            assert result.shape == background.shape
            # Should only have 3 channels (RGB)
            assert result.shape[2] == 3
        finally:
            if os.path.exists(temp_image):
                os.unlink(temp_image)
    
    @patch('moviepy.editor.TextClip')
    def test_create_text_clip(self, mock_textclip_class):
        """Test creating text clip."""
        mock_clip = MagicMock()
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.set_position.return_value = mock_clip
        mock_textclip_class.return_value = mock_clip
        
        result = VideoUtils.create_text_clip(
            "Test text", 5.0, (1920, 1080),
            font_size=60, color='white'
        )
        
        assert result is not None
        mock_clip.set_duration.assert_called_once_with(5.0)
    
    @patch('moviepy.editor.TextClip')
    def test_create_text_clip_error_handling(self, mock_textclip_class):
        """Test text clip creation error handling."""
        mock_textclip_class.side_effect = Exception("Font error")
        
        result = VideoUtils.create_text_clip(
            "Test", 5.0, (1920, 1080)
        )
        
        # Should return None on error
        assert result is None

