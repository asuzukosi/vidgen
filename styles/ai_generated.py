"""
ai-generated visuals video generator
creates modern explainer videos with:
- ai-generated custom images for each segment (dall-e or stable diffusion)
- ken burns effect on generated images
- text overlays synchronized with content
- professional transitions
- unique visuals that don't exist in the pdf
"""

import os
import sys
import json
from typing import Dict,  Optional
import numpy as np
from pathlib import Path
import hashlib
import argparse

# add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pillow 10.0.0+ compatibility fix for moviepy
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from openai import OpenAI

from core.video_utils import VideoUtils
from core.logger import get_logger

logger = get_logger(__name__)


class AIGeneratedGenerator:
    """generate videos with ai-generated custom visuals."""
    
    def __init__(self, config: Dict):
        """
        initialize ai-generated video generator.
        args:
            config: configuration dictionary
        """
        self.config = config
        self.width = config.get('video', {}).get('resolution', [1920, 1080])[0]
        self.height = config.get('video', {}).get('resolution', [1920, 1080])[1]
        self.fps = config.get('video', {}).get('fps', 30)
        
        # AI image generation settings
        self.image_generator = config.get('styles', {}).get('ai_generated', {}).get('image_generator', 'dalle')
        self.dalle_model = config.get('styles', {}).get('ai_generated', {}).get('dalle_model', 'dall-e-3')
        self.dalle_quality = config.get('styles', {}).get('ai_generated', {}).get('dalle_quality', 'standard')
        self.dalle_size = config.get('styles', {}).get('ai_generated', {}).get('dalle_size', '1792x1024')
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and self.image_generator == 'dalle':
            self.client = OpenAI(api_key=api_key)
            logger.info("initialized dall-e image generator")
        else:
            self.client = None
            logger.warning("openai api key not found. ai image generation will be skipped.")
        
        self.output_dir = os.path.join(
            config.get('output', {}).get('temp_directory', 'temp'),
            'ai_generated_images'
        )
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"initialized aigeneratedgenerator: {self.width}x{self.height} @ {self.fps}fps")
    
    def generate_video(self, script_with_audio: Dict, output_path: str) -> str:
        """
        generate video with ai-generated visuals.
        args:
            script_with_audio: script data with audio files
            output_path: path to save output video
        returns:
            path to generated video
        """
        logger.info("starting ai-generated video creation")
        
        # generate images for all segments first
        logger.info("generating ai images for segments...")
        script_with_images = self._generate_segment_images(script_with_audio)
        
        clips = []
        
        # create title card
        title_clip = self._create_title_card(script_with_audio.get('title', 'Untitled'))
        clips.append(title_clip)
        
        # create clips for each segment
        for i, segment in enumerate(script_with_images['segments'], 1):
            logger.info(f"creating video segment {i}/{len(script_with_images['segments'])}: {segment['title']}")
            
            segment_clip = self._create_segment_clip(segment, i)
            if segment_clip is not None:
                clips.append(segment_clip)
        
        # create end card
        end_clip = self._create_end_card()
        clips.append(end_clip)
        
        # concatenate all clips
        logger.info("Concatenating video clips...")
        final_video = concatenate_videoclips(clips, method='compose')
        
        # add full audio track
        full_audio_path = os.path.join(
            self.config.get('output', {}).get('temp_directory', 'temp'),
            'full_voiceover.mp3'
        )
        
        if os.path.exists(full_audio_path):
            logger.info("Adding audio track...")
            audio = AudioFileClip(full_audio_path)
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
            logger=None
        )
        
        logger.info(f"✓ AI-generated video created successfully: {output_path}")
        return output_path
    
    def _generate_segment_images(self, script_data: Dict) -> Dict:
        """
        generate ai images for all segments.
        args:
            script_data: script data with segments
        returns:
            script data with generated image paths added
        """
        if not self.client:
            logger.warning("Skipping AI image generation (no API key)")
            return script_data
        
        result = script_data.copy()
        
        for i, segment in enumerate(result['segments'], 1):
            # check if image already generated
            image_hash = hashlib.md5(segment['title'].encode()).hexdigest()[:10]
            image_path = os.path.join(self.output_dir, f"segment_{i}_{image_hash}.png")
            
            if os.path.exists(image_path):
                logger.info(f"Using cached image for segment {i}")
                segment['ai_generated_image'] = image_path
                continue

            # generate prompt
            prompt = self._create_image_prompt(segment)
            logger.info(f"Generating image for segment {i}: {segment['title']}")
            logger.debug(f"Prompt: {prompt}")
            
            # generate image
            image_path = self._generate_image_with_dalle(prompt, image_path)
            
            if image_path:
                segment['ai_generated_image'] = image_path
                logger.info(f"✓ Generated image saved to: {image_path}")
            else:
                logger.warning(f"Failed to generate image for segment {i}")
        
        return result
    
    def _create_image_prompt(self, segment: Dict) -> str:
        """
        create dall-e prompt from segment content.
        args:
            segment: segment data
        returns:
            image generation prompt
        """
        # extract key information
        title = segment['title']
        purpose = segment.get('purpose', '')
        visual_keywords = segment.get('visual_keywords', [])
        
        # build prompt
        prompt_parts = [
            "Create a professional, modern illustration for an educational video.",
            f"Topic: {title}",
        ]
        
        if purpose:
            prompt_parts.append(f"Purpose: {purpose}")
        
        if visual_keywords:
            keywords_str = ', '.join(visual_keywords[:3])
            prompt_parts.append(f"Visual elements: {keywords_str}")
        
        prompt_parts.extend([
            "Style: Clean, minimalist, professional",
            "Colors: Blue, white, with accent colors",
            "No text in the image",
            "High quality, suitable for HD video"
        ])
        
        return ' '.join(prompt_parts)
    
    def _generate_image_with_dalle(self, prompt: str, output_path: str) -> Optional[str]:
        """
        generate image using dall-e api.
        args:
            prompt: image generation prompt
            output_path: path to save generated image
        returns:
            path to saved image or None if failed
        """
        try:
            response = self.client.images.generate(
                model=self.dalle_model,
                prompt=prompt,
                size=self.dalle_size,
                quality=self.dalle_quality,
                n=1
            )
            
            # get image url
            image_url = response.data[0].url
            import requests
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # save image
            with open(output_path, 'wb') as f:
                f.write(image_response.content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating image with DALL-E: {str(e)}")
            return None
    
    def _create_title_card(self, title: str, duration: float = 3.0) -> VideoClip:
        """create title card clip."""
        logger.info("creating title card...")
        
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
        """create end card clip."""
        logger.info("Creating end card...")
        
        end_card = VideoUtils.create_end_card(
            self.width,
            self.height,
            message="Thank you for watching!",
            credits=[
                "created with pdf to video generator",
                "visuals generated by ai"
            ]
        )
        
        clip = ImageClip(end_card).set_duration(duration)
        clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
        
        return clip
    
    def _create_segment_clip(self, segment: Dict, segment_number: int) -> Optional[VideoClip]:
        """
        create video clip for segment with ai-generated visuals.
        args:
            segment: segment data
            segment_number: segment number
        returns:
            video clip or None
        """
        try:
            duration = segment.get('audio_duration', segment.get('duration', 45))
            # create base with ai-generated image or fallback
            if segment.get('ai_generated_image'):
                base_clip = self._create_ken_burns_clip(
                    segment['ai_generated_image'],
                    duration
                )
            else:
                # fallback to gradient background
                bg = VideoUtils.create_gradient_background(self.width, self.height)
                base_clip = ImageClip(bg).set_duration(duration)
            # create text overlay
            text_overlay = self._create_text_overlay(segment, segment_number, duration)
            # composite
            if text_overlay:
                composite = CompositeVideoClip(
                    [base_clip, text_overlay],
                    size=(self.width, self.height)
                )
            else:
                composite = base_clip
            
            composite = composite.set_duration(duration)
            
            # add audio
            audio_file = segment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio = AudioFileClip(audio_file)
                composite = composite.set_audio(audio)
                composite = composite.set_duration(audio.duration)
            # add transitions
            composite = composite.fx(fadein, 0.5).fx(fadeout, 0.5)
            return composite
            
        except Exception as e:
            logger.error(f"Error creating segment clip {segment_number}: {str(e)}")
            return None
    
    def _create_ken_burns_clip(self, image_path: str, duration: float) -> VideoClip:
        """
        create clip with ken burns effect (slow zoom and pan).
        
        args:
            image_path: path to image
            duration: duration in seconds
        returns:
            animated video clip
        """
        # load and resize image (slightly larger than video for pan room)
        img = VideoUtils.resize_image_to_fit(
            image_path,
            int(self.width * 1.2),
            int(self.height * 1.2),
            maintain_aspect=False
        )
        # convert to rgb
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img_array = np.array(img)
        # create clip with zoom and pan animation
        def make_frame(t):
            """create frame with ken burns effect."""
            progress = t / duration
            # zoom in slowly
            zoom = 1.0 + 0.1 * progress
            # pan slightly
            x_offset = int(self.width * 0.1 * progress)
            y_offset = int(self.height * 0.05 * progress)
            # calculate dimensions
            zoomed_width = int(self.width / zoom)
            zoomed_height = int(self.height / zoom)
            # crop with offset
            x_start = x_offset
            y_start = y_offset
            x_end = x_start + zoomed_width
            y_end = y_start + zoomed_height
            # ensure we don't go out of bounds
            x_start = max(0, min(x_start, img_array.shape[1] - zoomed_width))
            y_start = max(0, min(y_start, img_array.shape[0] - zoomed_height))
            x_end = x_start + zoomed_width
            y_end = y_start + zoomed_height
            # crop and resize
            cropped = img_array[y_start:y_end, x_start:x_end]
            # resize back to video dimensions
            pil_img = Image.fromarray(cropped)
            pil_img = pil_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            return np.array(pil_img)
        
        clip = VideoClip(make_frame, duration=duration)
        return clip
    
    def _create_text_overlay(self, segment: Dict, segment_number: int, 
                            duration: float) -> Optional[VideoClip]:
        """
        create text overlay for segment.
        args:
            segment: segment data
            segment_number: segment number
            duration: duration in seconds
        returns:
            text overlay clip or None
        """
        try:
            # create semi-transparent overlay at bottom
            overlay = Image.new('RGBA', (self.width, 300), (0, 0, 0, 180))
            # add title
            title_text = f"{segment_number}. {segment['title']}"
            overlay = VideoUtils.add_text_to_image(
                overlay,
                title_text,
                position=(50, 30),
                font_size=50,
                color=(255, 255, 255),
                max_width=self.width - 100
            )
            # add first key point
            key_points = segment.get('key_points', [])
            if key_points:
                overlay = VideoUtils.add_text_to_image(
                    overlay,
                    f"• {key_points[0]}",
                    position=(50, 120),
                    font_size=35,
                    color=(220, 220, 220),
                    max_width=self.width - 100
                )

            overlay_array = np.array(overlay)
            # create clip positioned at bottom
            clip = ImageClip(overlay_array).set_duration(duration)
            clip = clip.set_position(('center', 'bottom'))
            clip = clip.fx(fadein, 0.5)
            
            return clip
            
        except Exception as e:
            logger.warning(f"Could not create text overlay: {str(e)}")
            return None


def generate_ai_video(script_with_audio: Dict, config: Dict, 
                     output_path: str) -> str:
    """
    convenience function to generate ai-visual video.
    args:
        script_with_audio: script data with audio
        config: configuration dictionary
        output_path: output video path
    returns:
        path to generated video
    """
    generator = AIGeneratedGenerator(config)
    return generator.generate_video(script_with_audio, output_path)


if __name__ == "__main__":
    # test the ai-generated video generator
    parser = argparse.ArgumentParser(description='generate ai-generated video')
    parser.add_argument('script_path', type=str, help='path to script with audio')
    parser.add_argument('output_path', type=str, help='path to output video')
    args = parser.parse_args()
    
    # load script data
    print(f"\nloading script data...")
    with open(args.script_path, 'r') as f:
        script_data = json.load(f)
    
    print(f"loaded script with {len(script_data['segments'])} segments")
    
    # load config
    from core.config_loader import get_config
    config = get_config()
    
    # generate video
    print(f"\n=== Generating AI-Visual Video ===\n")
    print("Note: This will generate custom images for each segment using DALL-E.")
    print("This may take several minutes and will use API credits.\n")
    
    video_path = generate_ai_video(script_data, config.config, args.output_path)
    
    print(f"\n{'='*80}")
    print(f"** ai-generated video created! **")
    print(f"output: {video_path}")
    print(f"{'='*80}\n")

