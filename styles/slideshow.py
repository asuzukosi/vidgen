"""
slideshow video generator
creates presentation-style explainer videos with:
- slide backgrounds (gradient, solid, or images)
- text overlays synchronized with voiceover
- image displays (PDF and stock images)
- smooth transitions between segments
- title and end cards
"""

import os
import json
import argparse
import sys
from typing import Dict, Optional
import numpy as np

# add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, TextClip
)
from moviepy.video.fx import fadein, fadeout, crossfadein, crossfadeout
from PIL import Image, ImageDraw, ImageFont

from core.video_utils import VideoUtils
from core.logger import get_logger

logger = get_logger(__name__)


class SlideshowGenerator:
    """slideshow video generator."""
    
    def __init__(self, config: Dict):
        """
        initialize slideshow generator.
        args:
            config: configuration dictionary
        """
        self.config = config
        self.width = config.get('video', {}).get('resolution', [1920, 1080])[0]
        self.height = config.get('video', {}).get('resolution', [1920, 1080])[1]
        self.fps = config.get('video', {}).get('fps', 30)
        
        self.transition_duration = config.get('styles', {}).get('slideshow', {}).get('transition_duration', 0.5)
        self.background_type = config.get('styles', {}).get('slideshow', {}).get('background_type', 'gradient')
        
        logger.info(f"Initialized SlideshowGenerator: {self.width}x{self.height} @ {self.fps}fps")
    
    def generate_video(self, script_with_audio: Dict, output_path: str) -> str:
        """
        generate slideshow video from script and audio data.
        args:
            script_with_audio: script data with audio files
            output_path: path to save output video
        returns:
            path to generated video
        """
        logger.info("starting slideshow video generation")
        clips = []
        # create title card
        title_clip = self._create_title_card(script_with_audio.get('title', 'Untitled'))
        clips.append(title_clip)
        # create clips for each segment
        for i, segment in enumerate(script_with_audio['segments'], 1):
            logger.info(f"creating slide {i}/{len(script_with_audio['segments'])}: {segment['title']}")
            
            segment_clip = self._create_segment_clip(segment, i)
            if segment_clip:
                clips.append(segment_clip)
        
        # Create end card
        end_clip = self._create_end_card()
        clips.append(end_clip)
        
        # concatenate all clips
        logger.info("concatenating video clips...")
        final_video = concatenate_videoclips(clips, method='compose')
        
        # add full audio track if available
        full_audio_path = os.path.join(
            self.config.get('output', {}).get('temp_directory', 'temp'),
            'full_voiceover.mp3'
        )
        
        if os.path.exists(full_audio_path):
            logger.info("Adding audio track...")
            audio = AudioFileClip(full_audio_path)
            # adjust video duration to match audio (excluding title and end cards)
            final_video = final_video.set_audio(audio)
        
        # write video file
        logger.info(f"Writing video to {output_path}...")
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec=self.config.get('output', {}).get('codec', 'libx264'),
            audio_codec=self.config.get('output', {}).get('audio_codec', 'aac'),
            temp_audiofile='temp_audio.m4a',
            remove_temp=True,
            logger=None  # Suppress moviepy's verbose output
        )
        
        logger.info(f"** slideshow video generated successfully: {output_path} **")
        return output_path
    
    def _create_title_card(self, title: str, duration: float = 3.0) -> VideoClip:
        """
        create title card clip.
        args:
            title: video title
            duration: duration in seconds
        returns:
            video clip for title card
        """
        logger.info("Creating title card...")
        
        title_card = VideoUtils.create_title_card(
            self.width,
            self.height,
            title,
            subtitle="AI-Generated Explainer Video"
        )
        
        clip = ImageClip(title_card).set_duration(duration)
        clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
        
        return clip
    
    def _create_end_card(self, duration: float = 3.0) -> VideoClip:
        """
        create end card clip.
        args:
            duration: duration in seconds
        returns:
            video clip for end card
        """
        logger.info("Creating end card...")
        
        end_card = VideoUtils.create_end_card(
            self.width,
            self.height,
            message="Thank you for watching!",
            credits=[
                "Created with PDF to Video Generator",
                "Powered by AI"
            ]
        )
        
        clip = ImageClip(end_card).set_duration(duration)
        clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
        
        return clip
    
    def _create_segment_clip(self, segment: Dict, segment_number: int) -> Optional[VideoClip]:
        """
        create video clip for a segment.
        args:
            segment: segment data dictionary
            segment_number: segment number
        returns:
            video clip for segment or None if failed
        """
        try:
            # get duration from audio or estimate
            duration = segment.get('audio_duration', segment.get('duration', 45))
            
            # create background
            background = self._create_background(segment)
            
            # add image if available
            if segment.get('pdf_images') or segment.get('stock_image'):
                background = self._add_image_to_slide(background, segment)
            
            # add text overlay
            background = self._add_text_overlay(background, segment, segment_number)
            
            # create clip
            clip = ImageClip(background).set_duration(duration)
            
            # Add audio if available
            audio_file = segment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio = AudioFileClip(audio_file)
                clip = clip.set_audio(audio)
                # Ensure video duration matches audio
                clip = clip.set_duration(audio.duration)
            
            # Add transitions
            clip = clip.fx(crossfadein, self.transition_duration)
            clip = clip.fx(crossfadeout, self.transition_duration)
            
            return clip
            
        except Exception as e:
            logger.error(f"Error creating segment clip {segment_number}: {str(e)}")
            return None
    
    def _create_background(self, segment: Dict) -> np.ndarray:
        """
        create backgro und for slide.
        args:
            segment: segment data
        returns:
            background as numpy array
        """
        if self.background_type == 'gradient':
            # Use different gradient colors for variety
            colors = [
                ((30, 60, 114), (42, 82, 152)),   # Blue
                ((52, 73, 94), (93, 109, 126)),   # Dark blue-gray
                ((41, 128, 185), (52, 152, 219)), # Lighter blue
                ((142, 68, 173), (155, 89, 182)), # Purple
                ((39, 174, 96), (46, 204, 113)),  # Green
            ]
            color_pair = colors[hash(segment['title']) % len(colors)]
            return VideoUtils.create_gradient_background(
                self.width, self.height,
                color_pair[0], color_pair[1]
            )
        else:
            # Solid color
            return VideoUtils.create_solid_background(
                self.width, self.height,
                color=(45, 45, 45)
            )
    
    def _add_image_to_slide(self, background: np.ndarray, segment: Dict) -> np.ndarray:
        """
        add image to slide background.
        args:
            background: background numpy array
            segment: segment data
        returns:
            background with image composited
        """
        # Choose image (prefer PDF images, then stock)
        image_path = None
        
        if segment.get('pdf_images'):
            # Use first PDF image
            image_path = segment['pdf_images'][0]['filepath']
        elif segment.get('stock_image'):
            # Use stock image
            image_path = segment['stock_image']['filepath']
        
        if image_path and os.path.exists(image_path):
            try:
                # Composite image on right side of slide
                background = VideoUtils.composite_image_on_background(
                    background,
                    image_path,
                    position='right',
                    scale=0.4
                )
            except Exception as e:
                logger.warning(f"Could not add image: {str(e)}")
        
        return background
    
    def _add_text_overlay(self, background: np.ndarray, segment: Dict, 
                         segment_number: int) -> np.ndarray:
        """
        add text overlay to slide.
        args:
            background: background with possible image
            segment: segment data
            segment_number: segment number
        returns:
            background with text overlay
        """
        img = Image.fromarray(background)
        
        # add segment number and title
        title_text = f"{segment_number}. {segment['title']}"
        img = VideoUtils.add_text_to_image(
            img,
            title_text,
            position=(100, 100),
            font_size=70,
            color=(255, 255, 255),
            max_width=self.width - 200
        )
        
        # add key points (first 3)
        key_points = segment.get('key_points', [])[:3]
        if key_points:
            y_pos = 250
            for point in key_points:
                # Add bullet point
                point_text = f"• {point}"
                img = VideoUtils.add_text_to_image(
                    img,
                    point_text,
                    position=(120, y_pos),
                    font_size=40,
                    color=(220, 220, 220),
                    max_width=int(self.width * 0.5)
                )
                y_pos += 100
        
        return np.array(img)


def generate_slideshow_video(script_with_audio: Dict, config: Dict, 
                            output_path: str) -> str:
    """
    convenience function to generate slideshow video.
    
    args:
        script_with_audio: script data with audio
        config: configuration dictionary
        output_path: output video path
    returns:
        path to generated video
    """
    generator = SlideshowGenerator(config)
    return generator.generate_video(script_with_audio, output_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate a slideshow video from a script with audio."
    )
    parser.add_argument(
        "script_with_audio",
        help="Path to the script_with_audio.json file"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="output/slideshow_video.mp4",
        help="Output video path (default: output/slideshow_video.mp4)"
    )
    args = parser.parse_args()

    script_path = args.script_with_audio
    output_path = args.output

    # Load script data
    print(f"\n=== Loading Script Data ===")
    with open(script_path, 'r') as f:
        script_data = json.load(f)

    print(f"Loaded script with {len(script_data['segments'])} segments")

    # Load config
    from core.config_loader import get_config
    config = get_config()

    # Generate video
    print(f"\n=== Generating Slideshow Video ===\n")

    video_path = generate_slideshow_video(script_data, config.config, output_path)

    print(f"\n{'='*80}")
    print(f"✓ Slideshow video generated!")
    print(f"Output: {video_path}")
    print(f"{'='*80}\n")
