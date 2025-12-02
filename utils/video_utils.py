"""
vidgen video utilities module

provides shared utilities for all video style generators.
provides common functions for video composition, text rendering, and effects.
"""

# set of utility functions for video generation built on moviepy.
# Moviepy supports the following types of video clips:
# 1. VideoClip - for video files
# 2. ImageClip - for images
# 3. AudioClip - for audio files
# 4. TextClip - for text
# 5. CompositeVideoClip - for combining multiple video clips


from typing import Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import (
    TextClip
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from utils.logger import get_logger
from utils.font_loader import FontLoader

logger = get_logger(__name__)

class VideoUtils:
    """utility functions for video generation."""
    
    _font_loader: Optional[FontLoader] = None
    
    @classmethod
    def set_font_loader(cls, font_loader: FontLoader) -> None:
        """
        set font loader for video utils.
        
        args:
            font_loader: FontLoader instance
        """
        cls._font_loader = font_loader
    
    @staticmethod
    def create_gradient_background(width: int, height: int, 
                                   color1: Tuple[int, int, int] = (254, 234, 201),
                                   color2: Tuple[int, int, int] = (255, 205, 201)) -> np.ndarray:
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
                         align: str = 'left',
                         font_type: str = 'default') -> Image.Image:
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
            font_type: font type to use ('title', 'body', 'subtitle', 'default')
        returns:
            pil image with text added
        """
        img = image.copy()
        draw = ImageDraw.Draw(img)
        
        # load font using font loader if available
        if VideoUtils._font_loader:
            if font_type == 'title':
                font = VideoUtils._font_loader.get_title_font(font_size)
            elif font_type == 'body':
                font = VideoUtils._font_loader.get_body_font(font_size)
            elif font_type == 'subtitle':
                font = VideoUtils._font_loader.get_subtitle_font(font_size)
            else:
                font = VideoUtils._font_loader.get_default_font(font_size)
        else:
            # fallback to old method if no font loader
            try:
                font = ImageFont.truetype("/Users/kosisochukwuasuzu/Developer/vidgen/fonts/BebasNeue-Regular.ttf", font_size)
                logger.info(f"loaded font: /Users/kosisochukwuasuzu/Developer/vidgen/fonts/BebasNeue-Regular.ttf (size: {font_size})")
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                    logger.info(f"loaded font: arial.ttf (size: {font_size})")
                except:
                    font = ImageFont.load_default()
                    logger.info(f"loaded default font (size: {font_size})")
        
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
                         subtitle: Optional[str] = None) -> np.ndarray:
        """
        create a title card for video.
        args:
            width: video width
            height: video height
            title: main title text
            subtitle: optional subtitle
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
            position=(100, title_y),
            font_size=80,
            color=(255, 255, 255),
            max_width=width,
            align='left',
            font_type='title'
        )
        
        # add subtitle if provided
        if subtitle:
            img = VideoUtils.add_text_to_image(
                img, subtitle,
                position=(100, height // 2 + 50),
                font_size=30,
                color=(100, 100, 100),
                max_width=width - 200,
                align='left',
                font_type='subtitle'
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
            align='center',
            font_type='title'
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
                    align='center',
                    font_type='subtitle'
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
                                     scale: Optional[float] = None,
                                     width_percent: Optional[float] = None) -> np.ndarray:
        """
        composite an image onto a background.
        args:
            background: background as numpy array
            image_path: path to image file
            position: 'center', 'left', 'right', 'top', 'bottom'
            scale: scale factor for image (0-1) - used if width_percent not provided
            width_percent: percentage of background width to use (0-1) - takes precedence over scale
        returns:
            composited image as numpy array
        """
        bg_height, bg_width = background.shape[:2]
        
        # calculate max dimensions for image
        if width_percent is not None:
            # use width percentage - image takes up specified % of horizontal space
            max_width = int(bg_width * width_percent)

        elif scale is not None:
            # use scale factor (backward compatibility)
            max_width = int(bg_width * scale)
        else:
            # default to 60% scale
            max_width = int(bg_width * 0.6)        
        # resize image
        img = VideoUtils.resize_image_to_fit(image_path, 
                                             max_width, 
                                             bg_height)
        img_array = np.array(img)
        
        # handle rgba images
        if img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]
        
        img_height, img_width = img_array.shape[:2]
        
        # calculate position
        if position == 'center':
            x = (bg_width - img_width) // 2
            y = 10
        elif position == 'left':
            x = 50
            y = 10
        elif position == 'right':
            # for right position with width_percent, align to right edge with padding
            x = bg_width - img_width - 50
            y = 10
        elif position == 'top':
            x = (bg_width - img_width) // 2
            y = 10
        elif position == 'bottom':
            x = (bg_width - img_width) // 2
            y = 10
        else:
            x = (bg_width - img_width) // 2
            y = 10
        
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
