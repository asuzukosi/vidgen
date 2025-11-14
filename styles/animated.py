"""
animated motion graphics generator
creates dynamic explainer videos with:
- animated text (fade in, slide, typewriter effects)
- shape animations (circles, arrows, underlines)
- camera movements (zoom, pan)
- ken burns effect on images
- smooth, professional transitions
"""

import os
import sys
from typing import Dict, List, Optional
import numpy as np
import argparse
import json

# add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pillow 10.0.0+ compatibility fix for moviepy
from PIL import Image, ImageDraw
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from core.video_utils import VideoUtils
from core.logger import get_logger

logger = get_logger(__name__)


class AnimatedGenerator:
    """
    generate animated motion graphics videos
    """
    def __init__(self, config: Dict):
        """
        initialize animated generator
        args:
            config: configuration dictionary
        """
        self.config = config
        self.width = config.get('video', {}).get('resolution', [1920, 1080])[0]
        self.height = config.get('video', {}).get('resolution', [1920, 1080])[1]
        self.fps = config.get('video', {}).get('fps', 30)
        
        self.animation_speed = config.get('styles', {}).get('animated', {}).get('animation_speed', 1.0)
        self.enable_shapes = config.get('styles', {}).get('animated', {}).get('enable_shapes', True)
        self.camera_movement = config.get('styles', {}).get('animated', {}).get('camera_movement', True)
        
        logger.info(f"initialized animatedgenerator: {self.width}x{self.height} @ {self.fps}fps")
    
    def generate_video(self, script_with_audio: Dict, output_path: str) -> str:
        """
        generate animated video from script and audio data
        args:
            script_with_audio: script data with audio files
            output_path: path to save output video
        returns:
            path to generated video
        """
        logger.info("starting animated video generation")
        
        clips = []
        
        # create animated title card
        title_clip = self._create_animated_title_card(
            script_with_audio.get('title', 'Untitled')
        )
        clips.append(title_clip)
        
        # create animated clips for each segment
        for i, segment in enumerate(script_with_audio['segments'], 1):
            logger.info(f"Creating animated segment {i}/{len(script_with_audio['segments'])}: {segment['title']}")
            
            segment_clip = self._create_animated_segment(segment, i)
            if segment_clip is not None:
                clips.append(segment_clip)
        
        # create animated end card
        end_clip = self._create_animated_end_card()
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
            final_video = final_video.set_audio(audio)
        
        # write video file
        logger.info(f"writing video to {output_path}...")
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec=self.config.get('output', {}).get('codec', 'libx264'),
            audio_codec=self.config.get('output', {}).get('audio_codec', 'aac'),
            temp_audiofile='temp_audio.m4a',
            remove_temp=True,
            logger=None
        )
        
        logger.info(f"** animated video generated successfully: {output_path} **")
        return output_path
    
    def _create_animated_title_card(self, title: str, duration: float = 3.0) -> VideoClip:
        """
        create animated title card with fade and zoom effects
        args:
            title: video title
            duration: duration in seconds
        returns:
            animated video clip
        """
        logger.info("creating animated title card...")
        # create base title card
        title_card = VideoUtils.create_title_card(
            self.width,
            self.height,
            title,
            subtitle="AI-Generated Explainer Video"
        )
        # create clip with animation
        clip = ImageClip(title_card).set_duration(duration)
        # add zoom in effect
        if self.camera_movement:
            clip = clip.resize(lambda t: 1 + 0.1 * (t / duration))
        # add fade
        clip = clip.fx(fadein, 1.0).fx(fadeout, 0.5)
        return clip
    
    def _create_animated_end_card(self, duration: float = 3.0) -> VideoClip:
        """
        create animated end card
        args:
            duration: duration in seconds
        returns:
            animated video clip
        """
        logger.info("Creating animated end card...")
        
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
    
    def _create_animated_segment(self, segment: Dict, segment_number: int) -> Optional[VideoClip]:
        """
        create animated video clip for a segment
        args:
            segment: segment data dictionary
            segment_number: segment number
        returns:
            animated video clip or None if failed
        """
        try:
            duration = segment.get('audio_duration', segment.get('duration', 45))
            
            # create animated background
            background_clip = self._create_animated_background(duration)
            # create text animations
            text_clips = self._create_animated_text(segment, segment_number, duration)
            # create image animation if available
            image_clip = self._create_animated_image(segment, duration)
            # composite all elements
            clips_to_composite = [background_clip]
            if image_clip is not None:
                clips_to_composite.append(image_clip)
            clips_to_composite.extend(text_clips)
            composite = CompositeVideoClip(clips_to_composite, size=(self.width, self.height))
            composite = composite.set_duration(duration)
            # add audio
            audio_file = segment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio = AudioFileClip(audio_file)
                composite = composite.set_audio(audio)
                composite = composite.set_duration(audio.duration)

            return composite
            
        except Exception as e:
            logger.error(f"error creating animated segment {segment_number}: {str(e)}")
            return None
    
    def _create_animated_background(self, duration: float) -> VideoClip:
        """
        create animated background with subtle movement
        args:
            duration: duration in seconds
        returns:
            animated background video clip
        """
        # create gradient background
        bg_array = VideoUtils.create_gradient_background(
            int(self.width * 1.2),  # Slightly larger for pan effect
            int(self.height * 1.2),
            color1=(30, 60, 114),
            color2=(42, 82, 152)
        )
        
        def make_frame(t):
            """Create frame with subtle pan effect."""
            # slow pan effect
            x_offset = int(self.width * 0.1 * (t / duration))
            y_offset = int(self.height * 0.05 * (t / duration))
            # crop to video size with offset
            return bg_array[
                y_offset:y_offset + self.height,
                x_offset:x_offset + self.width
            ]
        
        if self.camera_movement:
            clip = VideoClip(make_frame, duration=duration)
        else:
            # Static background
            clip = ImageClip(bg_array[:self.height, :self.width]).set_duration(duration)
        
        return clip
    
    def _create_animated_text(self, segment: Dict, segment_number: int, 
                             duration: float) -> List[VideoClip]:
        """
        create animated text overlays
        args:
            segment: segment data
            segment_number: segment number
            duration: duration in seconds
        returns:
            list of animated text clips
        """
        text_clips = []
        
        # animated title - slides in from left
        title_text = f"{segment_number}. {segment['title']}"
        title_img = self._create_text_image(
            title_text,
            font_size=70,
            max_width=self.width - 200
        )
        
        if title_img is not None:
            title_clip = ImageClip(title_img).set_duration(duration)
            
            # slide in animation
            title_clip = title_clip.set_position(
                lambda t: (max(-500, -500 + int(600 * min(1, t / 0.5))), 100)
            )
            
            # fade in
            title_clip = title_clip.fx(fadein, 0.5)
            text_clips.append(title_clip)
        
        # animated key points - fade in one by one
        key_points = segment.get('key_points', [])[:3]
        y_pos = 300
        
        for i, point in enumerate(key_points):
            delay = 0.5 + i * 0.3  # Stagger animations
            point_text = f"• {point}"
            
            point_img = self._create_text_image(
                point_text,
                font_size=40,
                max_width=int(self.width * 0.5)
            )
            
            if point_img is not None:
                point_clip = ImageClip(point_img).set_duration(duration - delay)
                point_clip = point_clip.set_position((120, y_pos))
                point_clip = point_clip.set_start(delay)
                
                # fade in with slight slide
                point_clip = point_clip.fx(fadein, 0.3)
                
                # add underline animation if enabled
                if self.enable_shapes and i == 0:
                    underline = self._create_underline_animation(duration - delay, y_pos + 50)
                    underline = underline.set_start(delay + 0.3)
                    text_clips.append(underline)
                
                text_clips.append(point_clip)
            
            y_pos += 100
        
        return text_clips
    
    def _create_text_image(self, text: str, font_size: int = 60, 
                          max_width: Optional[int] = None) -> Optional[np.ndarray]:
        """
        create text as image for animation
        args:
            text: text to render
            font_size: font size
            max_width: maximum width
        returns:
            text as numpy array or None
        """
        try:
            # create transparent image
            img = Image.new('RGBA', (self.width, 200), (0, 0, 0, 0))
            
            img = VideoUtils.add_text_to_image(
                img,
                text,
                position=(0, 0),
                font_size=font_size,
                color=(255, 255, 255),
                max_width=max_width
            )
            
            # convert RGBA to RGB for moviepy compatibility
            if img.mode == 'RGBA':
                # create RGB background
                rgb_img = Image.new('RGB', img.size, (0, 0, 0))
                # composite RGBA onto RGB background
                rgb_img.paste(img, mask=img.split()[3])  # use alpha channel as mask
                img = rgb_img
            
            return np.array(img)
        except Exception as e:
            logger.warning(f"could not create text image: {str(e)}")
            return None
    
    def _create_animated_image(self, segment: Dict, duration: float) -> Optional[VideoClip]:
        """
        create animated image with Ken Burns effect
        args:
            segment: segment data
            duration: duration in seconds
        returns:
            animated image clip or None
        """
        # get image path
        image_path = None
        
        if segment.get('pdf_images'):
            image_path = segment['pdf_images'][0]['filepath']
        elif segment.get('stock_image'):
            image_path = segment['stock_image']['filepath']
        
        if not image_path or not os.path.exists(image_path):
            return None
        
        try:
            # resize image
            img = VideoUtils.resize_image_to_fit(
                image_path,
                int(self.width * 0.4),
                int(self.height * 0.6)
            )
            # convert to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img_array = np.array(img)
            # create clip with Ken Burns effect (slow zoom)
            clip = ImageClip(img_array).set_duration(duration)
            if self.camera_movement:
                # zoom in slowly
                clip = clip.resize(lambda t: 1 + 0.05 * (t / duration))
            # position on right side
            clip = clip.set_position(('right', 'center'))
            # fade in and out
            clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
            return clip
            
        except Exception as e:
            logger.warning(f"Could not create animated image: {str(e)}")
            return None
    
    def _create_underline_animation(self, duration: float, y_pos: int) -> VideoClip:
        """
        create animated underline that draws o
        args:
            duration: duration in seconds
            y_pos: y position
        returns:
            animated underline clip
        """
        def make_frame(t):
            """create underline frame."""
            # calculate progress
            progress = min(1.0, t / 0.5)  # Draw over 0.5 seconds
            
            # create image
            img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # draw underline
            line_width = int(400 * progress)
            draw.line(
                [(120, y_pos), (120 + line_width, y_pos)],
                fill=(255, 200, 0, 255),
                width=3
            )
            
            # convert RGBA to RGB for moviepy compatibility
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (0, 0, 0))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            return np.array(img)
        
        clip = VideoClip(make_frame, duration=duration)
        return clip


def generate_animated_video(script_with_audio: Dict, config: Dict, 
                           output_path: str) -> str:
    """
    convenience function to generate animated video.
    args:
        script_with_audio: script data with audio
        config: configuration dictionary
        output_path: output video path
    returns:
        path to generated video
    """
    generator = AnimatedGenerator(config)
    return generator.generate_video(script_with_audio, output_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate an animated video from script and audio data. "
                    "First run Phases 1-4 to generate the script and audio."
    )
    parser.add_argument(
        "script_path",
        type=str,
        help="path to script_with_audio.json"
    )
    parser.add_argument(
        "output_path",
        nargs="?",
        default="output/animated_video.mp4",
        help="output video file path (default: output/animated_video.mp4)"
    )
    args = parser.parse_args()

    script_path = args.script_path
    output_path = args.output_path

    # Load script data
    print(f"\n** loading script data **")
    with open(script_path, 'r') as f:
        script_data = json.load(f)

    print(f"loaded script with {len(script_data['segments'])} segments")
    # load config
    from core.config_loader import get_config
    config = get_config()
    # generate video
    print(f"\n** generating animated video **")
    video_path = generate_animated_video(script_data, config.config, output_path)

    print(f"\n** animated video generated successfully: {output_path} **")
    print(f"output: {video_path}")
    print(f"** animated video generated successfully: {output_path} **")
