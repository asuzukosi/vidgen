"""
vidgen video utilities module

provides shared utilities for all video style generators.
provides common functions for video composition, text rendering, and effects.
"""

from typing import Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import (
    TextClip
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from core.logger import get_logger
logger = get_logger(__name__)

class VideoUtils:
    """utility functions for video generation."""
    
    @staticmethod
    def create_gradient_background(width: int, height: int, 
                                   color1: Tuple[int, int, int] = (30, 60, 114),
                                   color2: Tuple[int, int, int] = (42, 82, 152)) -> np.ndarray:
        """
        create a gradient background.
        args:
            width: image width
            height: image height
            color1: start color (RGB)
            color2: end color (RGB)
        returns:
            numpy array representing the image
        """
        gradient = np.zeros((height, width, 3), dtype=np.uint8)
        
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            gradient[y, :] = [r, g, b]
        
        return gradient
    
    @staticmethod
    def create_solid_background(width: int, height: int,
                               color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
        """
        create a solid color background.
        args:
            width: image width
            height: image height
            color: rgb color tuple
        returns:
            numpy array representing the image
        """
        background = np.zeros((height, width, 3), dtype=np.uint8)
        background[:] = color
        return background
    
    @staticmethod
    def resize_image_to_fit(image_path: str, max_width: int, max_height: int,
                           maintain_aspect: bool = True) -> Image.Image:
        """
        resize image to fit within dimensions while maintaining aspect ratio.
        args:
            image_path: path to image file
            max_width: maximum width
            max_height: maximum height
            maintain_aspect: whether to maintain aspect ratio
        returns:
            resized pil image
        """
        img = Image.open(image_path)
        
        if maintain_aspect:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((max_width, max_height), Image.Resampling.LANCZOS)
        
        return img
    
    @staticmethod
    def add_text_to_image(image: Image.Image, text: str, 
                         position: Tuple[int, int],
                         font_size: int = 60,
                         color: Tuple[int, int, int] = (255, 255, 255),
                         max_width: Optional[int] = None,
                         align: str = 'left') -> Image.Image:
        """
        add text to a pil image.
        args:
            image: pil image
            text: text to add
            position: (x, y) position
            font_size: Font size
            color: Text color RGB
            max_width: Maximum width for text wrapping
            align: Text alignment ('left', 'center', 'right')
        returns:
            pil image with text added
        """
        img = image.copy()
        draw = ImageDraw.Draw(img)
        
        # try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # wrap text if max_width specified
        if max_width:
            text = VideoUtils._wrap_text(text, font, max_width, draw)
        
        # draw text with shadow for better visibility
        shadow_offset = 2
        draw.text((position[0] + shadow_offset, position[1] + shadow_offset), 
                 text, font=font, fill=(0, 0, 0), align=align)
        draw.text(position, text, font=font, fill=color, align=align)
        
        return img
    
    @staticmethod
    def _wrap_text(text: str, font, max_width: int, draw) -> str:
        """wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    @staticmethod
    def create_title_card(width: int, height: int, title: str,
                         subtitle: Optional[str] = None,
                         background_color: Tuple[int, int, int] = (30, 60, 114)) -> np.ndarray:
        """
        create a title card for video.
        args:
            width: video width
            height: video height
            title: main title text
            subtitle: optional subtitle
            background_color: background color rgb
        returns:
            numpy array representing the title card
        """
        # create gradient background
        background = VideoUtils.create_gradient_background(width, height)
        img = Image.fromarray(background)
        
        # add title
        title_y = height // 2 - 100 if subtitle else height // 2
        img = VideoUtils.add_text_to_image(
            img, title,
            position=(width // 2, title_y),
            font_size=80,
            color=(255, 255, 255),
            max_width=width - 100,
            align='center'
        )
        
        # add subtitle if provided
        if subtitle:
            img = VideoUtils.add_text_to_image(
                img, subtitle,
                position=(width // 2, height // 2 + 50),
                font_size=40,
                color=(200, 200, 200),
                max_width=width - 100,
                align='center'
            )
        
        return np.array(img)
    
    @staticmethod
    def create_end_card(width: int, height: int, message: str = "Thank you for watching!",
                       credits: Optional[List[str]] = None) -> np.ndarray:
        """
        create an end card for video.
        args:
            width: video width
            height: video height
            message: main message
            credits: optional list of credit lines
        returns:
            numpy array representing the end card
        """
        background = VideoUtils.create_gradient_background(width, height)
        img = Image.fromarray(background)
        img = VideoUtils.add_text_to_image(
            img, message,
            position=(width // 2, height // 2 - 100),
            font_size=60,
            color=(255, 255, 255),
            max_width=width - 100,
            align='center'
        )
        if credits:
            credit_y = height // 2 + 50
            for credit in credits:
                img = VideoUtils.add_text_to_image(
                    img, credit,
                    position=(width // 2, credit_y),
                    font_size=30,
                    color=(180, 180, 180),
                    max_width=width - 100,
                    align='center'
                )
                credit_y += 40
        
        return np.array(img)
    
    @staticmethod
    def add_fade_transition(clip, fade_duration: float = 0.5):
        """
        add fade in and fade out to a clip.
        args:
            clip: video clip
            fade_duration: duration of fade in seconds
        returns:
            clip with fade effects
        """
        return clip.fx(fadein, fade_duration).fx(fadeout, fade_duration)
    
    @staticmethod
    def composite_image_on_background(background: np.ndarray, 
                                     image_path: str,
                                     position: str = 'center',
                                     scale: float = 0.6) -> np.ndarray:
        """
        composite an image onto a background.
        args:
            background: background as numpy array
            image_path: path to image file
            position: 'center', 'left', 'right', 'top', 'bottom'
            scale: scale factor for image (0-1)
        returns:
            composited image as numpy array
        """
        bg_height, bg_width = background.shape[:2]
        
        # calculate max dimensions for image
        max_width = int(bg_width * scale)
        max_height = int(bg_height * scale)
        
        # resize image
        img = VideoUtils.resize_image_to_fit(image_path, max_width, max_height)
        img_array = np.array(img)
        
        # handle rgba images
        if img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]
        
        img_height, img_width = img_array.shape[:2]
        
        # calculate position
        if position == 'center':
            x = (bg_width - img_width) // 2
            y = (bg_height - img_height) // 2
        elif position == 'left':
            x = 50
            y = (bg_height - img_height) // 2
        elif position == 'right':
            x = bg_width - img_width - 50
            y = (bg_height - img_height) // 2
        elif position == 'top':
            x = (bg_width - img_width) // 2
            y = 50
        elif position == 'bottom':
            x = (bg_width - img_width) // 2
            y = bg_height - img_height - 50
        else:
            x = (bg_width - img_width) // 2
            y = (bg_height - img_height) // 2
        
        # create result
        result = background.copy()
        result[y:y+img_height, x:x+img_width] = img_array
        
        return result
    
    @staticmethod
    def create_text_clip(text: str, duration: float, size: Tuple[int, int],
                        font_size: int = 60, color: str = 'white',
                        bg_color: str = 'transparent',
                        position: Tuple = ('center', 'center')) -> TextClip:
        """
        create a text clip for video.
        args:
            text: text to display
            duration: duration in seconds
            size: (width, height) of video
            font_size: font size
            color: text color
            bg_color: background color
            position: position tuple
        returns:
            textclip object
        """
        try:
            txt_clip = TextClip(
                text,
                fontsize=font_size,
                color=color,
                bg_color=bg_color,
                size=size,
                method='caption'
            ).set_duration(duration).set_position(position)
            return txt_clip
        except Exception as e:
            logger.warning(f"error creating textclip: {e}")
            # Fallback: return None
            return None


def test_utils():
    """test video utilities."""
    print("\n**** testing video utils ****\n")
    
    # test gradient background
    gradient = VideoUtils.create_gradient_background(1920, 1080)
    print(f"created gradient background: {gradient.shape}")
    
    # test solid background
    solid = VideoUtils.create_solid_background(1920, 1080, (50, 50, 50))
    print(f"created solid background: {solid.shape}")
    
    # Test title card
    title_card = VideoUtils.create_title_card(
        1920, 1080,
        "Test Video",
        "A subtitle"
    )
    print(f"created title card: {title_card.shape}")
    
    # test end card
    end_card = VideoUtils.create_end_card(
        1920, 1080,
        "Thanks for watching!",
        ["Created with PDF to Video Generator", "github.com/vidgen"]
    )
    print(f"created end card: {end_card.shape}")
    
    print("\n**** all tests passed ****\n")


if __name__ == "__main__":
    test_utils()

