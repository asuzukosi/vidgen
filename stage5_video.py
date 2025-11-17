#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 5: VIDEO GENERATION TEST - ALL STYLES

PURPOSE:
    Generate the final video using various visual styles:
    - Slideshow: Classic presentation with text and images
    - Animated: Motion graphics with dynamic effects
    - AI Generated: Custom DALL-E visuals for each segment
    - Combined: AI-selected mix of all styles

APPROACH BY STYLE:

1. SLIDESHOW STYLE:
   - Gradient backgrounds or solid colors
   - Text overlays synchronized with voiceover
   - Image displays (PDF + stock images)
   - Crossfade transitions between segments
   - Title and end cards

2. ANIMATED STYLE:
   - Animated text (slide in, fade effects)
   - Shape animations (underlines, accents)
   - Camera movements (zoom, pan)
   - Ken Burns effect on images
   - Staggered animations for visual interest

3. AI GENERATED STYLE:
   - DALL-E generates custom images per segment
   - Images based on content and keywords
   - Ken Burns effect on AI images
   - Text overlays with generated backgrounds
   - Unique visuals created on-demand

4. COMBINED STYLE:
   - AI analyzes each segment
   - Selects best style per segment:
     * Slideshow: Introduction, data-heavy
     * Animated: Concepts, processes
     * AI Generated: Abstract ideas, vision
   - Creates varied, engaging video

OUTPUT:
    - Final video: output/<pdf_name>_<style>.mp4
    - Console progress updates
    - Video statistics

OPTIONS:
    --style STYLE    Video style: slideshow, animated, ai_generated, combined
    --use-cached     Use previously generated script and audio
    --output PATH    Custom output path

USAGE:
    python test_stage5_video.py <pdf_file> --style <style> [options]
    
EXAMPLES:
    python test_stage5_video.py document.pdf --style slideshow
    python test_stage5_video.py document.pdf --style animated
    python test_stage5_video.py document.pdf --style ai_generated
    python test_stage5_video.py document.pdf --style combined
    python test_stage5_video.py document.pdf --style slideshow --use-cached
    python test_stage5_video.py document.pdf --style animated --output my_video.mp4
"""

import sys
import os
import json
from pathlib import Path
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logging, get_logger
from core.config_loader import get_config
from styles.slideshow import generate_slideshow_video
from styles.animated import generate_animated_video
from styles.ai_generated import generate_ai_video
from styles.combined import generate_combined_video

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def test_video_generation(pdf_path: str, style: str, use_cached: bool = False, output_path: str = None):
    """
    Test video generation with specified style.
    
    Args:
        pdf_path: Path to PDF file
        style: Video style
        use_cached: Use cached script and audio
        output_path: Custom output path
    """
    print("\n" + "="*80)
    print(f"STAGE 5: VIDEO GENERATION - {style.upper()} STYLE")
    print("="*80 + "\n")
    
    config = get_config()
    
    try:
        temp_dir = 'temp'
        script_audio_path = os.path.join(temp_dir, 'script_with_audio.json')
        
        # Load script with audio
        if not os.path.exists(script_audio_path):
            print("❌ Error: Script with audio not found")
            print("Run test_stage4_script.py first")
            return False
        
        print("📦 Loading script and audio data...")
        with open(script_audio_path, 'r') as f:
            script_with_audio = json.load(f)
        print(f"✓ Loaded {len(script_with_audio['segments'])} segments with audio\n")
        
        # Determine output path
        if not output_path:
            output_dir = config.get('output.directory', 'output')
            Path(output_dir).mkdir(exist_ok=True)
            pdf_name = Path(pdf_path).stem
            output_path = os.path.join(output_dir, f"{pdf_name}_{style}.mp4")
        
        # Display style info
        print("="*80)
        print(f"{style.upper()} STYLE APPROACH")
        print("="*80)
        
        style_descriptions = {
            'slideshow': """
- Gradient or solid color backgrounds
- Text overlays synchronized with audio
- Image displays (PDF + stock images)
- Smooth crossfade transitions
- Professional title and end cards
            """,
            'animated': """
- Animated text with slide and fade effects
- Shape animations (underlines, accents)
- Camera movements (zoom, pan)
- Ken Burns effect on images
- Staggered animations for visual interest
            """,
            'ai_generated': """
- DALL-E generates custom images per segment
- Images based on content keywords
- Ken Burns effect on AI visuals
- Text overlays with generated backgrounds
- Unique visuals for each segment
            """,
            'combined': """
- AI analyzes each segment
- Selects optimal style per segment:
  * Slideshow: Introductions, data-heavy
  * Animated: Concepts, processes
  * AI Generated: Abstract ideas, vision
- Creates varied, engaging experience
            """
        }
        
        print(style_descriptions.get(style, "Custom style"))
        print("="*80 + "\n")
        
        # Generate video
        print(f"🎬 Generating {style} video...")
        print(f"Output: {output_path}\n")
        
        if style == 'slideshow':
            video_path = generate_slideshow_video(script_with_audio, config.config, output_path)
        elif style == 'animated':
            video_path = generate_animated_video(script_with_audio, config.config, output_path)
        elif style == 'ai_generated':
            video_path = generate_ai_video(script_with_audio, config.config, output_path)
        elif style == 'combined':
            video_path = generate_combined_video(script_with_audio, config.config, output_path)
        else:
            print(f"❌ Error: Unknown style '{style}'")
            return False
        
        # Display results
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            
            print("\n" + "="*80)
            print("✅ STAGE 5 COMPLETE - VIDEO GENERATED!")
            print("="*80)
            print(f"Style: {style}")
            print(f"Output: {video_path}")
            print(f"Size: {file_size:.2f} MB")
            print("="*80)
            print("\n🎉 SUCCESS! Your explainer video is ready!")
            print(f"📹 Watch it at: {video_path}")
            print("="*80 + "\n")
            
            return True
        else:
            print("\n❌ Error: Video file was not created")
            return False
        
    except Exception as e:
        print(f"\n❌ Error during video generation: {str(e)}")
        logger.error(f"Error: {str(e)}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="STAGE 5: VIDEO GENERATION - Generate a video from a PDF using various styles."
    )
    parser.add_argument(
        "pdf_file",
        metavar="pdf_file",
        type=str,
        help="Path to the PDF file."
    )
    parser.add_argument(
        "--style",
        required=True,
        choices=["slideshow", "animated", "ai_generated", "combined"],
        help="Video style to use. Choices: slideshow, animated, ai_generated, combined."
    )
    parser.add_argument(
        "--use-cached",
        action="store_true",
        help="Use previously generated script and audio."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output path for the generated video."
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    pdf_path = args.pdf_file
    style = args.style
    use_cached = args.use_cached
    output_path = args.output

    success = test_video_generation(pdf_path, style, use_cached, output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

