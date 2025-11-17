"""
Combined Style Video Generator

Intelligently combines all three video styles (slideshow, animated, ai_generated)
based on AI analysis of each segment's content. Uses GPT-4 to determine the best
visual approach for each segment, creating the most dynamic and engaging videos.

Features:
- AI-powered style selection per segment
- Mix of slideshow, animated, and AI-generated visuals
- Intelligent decision-making based on content type
- Seamless transitions between different styles
- Most engaging and varied output
"""

import os
import sys
from typing import Dict, List, Optional
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moviepy.editor import concatenate_videoclips, AudioFileClip
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape

from styles.slideshow import SlideshowGenerator
from styles.animated import AnimatedGenerator
from styles.ai_generated import AIGeneratedGenerator
from core.logger import get_logger

logger = get_logger(__name__)


class CombinedGenerator:
    """Generate videos with AI-selected combination of all styles."""
    
    def __init__(self, config: Dict):
        """
        Initialize combined generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.width = config.get('video', {}).get('resolution', [1920, 1080])[0]
        self.height = config.get('video', {}).get('resolution', [1920, 1080])[1]
        self.fps = config.get('video', {}).get('fps', 30)
        
        # Initialize OpenAI client for style selection
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not found. Will use default style selection.")
        
        # Initialize all style generators
        self.slideshow_gen = SlideshowGenerator(config)
        self.animated_gen = AnimatedGenerator(config)
        self.ai_gen = AIGeneratedGenerator(config)
        
        # initialize jinja2 environment for prompt templates
        prompts_dir = Path(__file__).parent.parent / 'prompts'
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        logger.info(f"Initialized CombinedGenerator: {self.width}x{self.height} @ {self.fps}fps")
    
    def generate_video(self, script_with_audio: Dict, output_path: str) -> str:
        """
        Generate video with AI-selected combination of styles.
        
        Args:
            script_with_audio: Script data with audio files
            output_path: Path to save output video
            
        Returns:
            Path to generated video
        """
        logger.info("Starting combined-style video generation")
        logger.info("AI will select the best visual approach for each segment\n")
        
        # Step 1: Analyze segments and assign styles
        logger.info("--- AI Style Analysis ---")
        segments_with_styles = self._assign_styles_to_segments(script_with_audio)
        
        # Display style assignments
        logger.info("\nStyle Assignments:")
        for i, segment in enumerate(segments_with_styles['segments'], 1):
            style = segment.get('selected_style', 'slideshow')
            reason = segment.get('style_reason', 'Default')
            logger.info(f"  {i}. {segment['title']}: {style.upper()}")
            logger.info(f"     Reason: {reason}")
        logger.info("")
        
        # Step 2: Generate clips for each segment using assigned style
        logger.info("--- Generating Segments ---")
        clips = []
        
        # Title card (always slideshow style)
        logger.info("Creating title card...")
        title_clip = self.slideshow_gen._create_title_card(
            script_with_audio.get('title', 'Untitled')
        )
        clips.append(title_clip)
        
        # Generate each segment with its assigned style
        for i, segment in enumerate(segments_with_styles['segments'], 1):
            style = segment.get('selected_style', 'slideshow')
            logger.info(f"Segment {i}/{len(segments_with_styles['segments'])}: {segment['title']} ({style})")
            
            clip = self._generate_segment_with_style(segment, i, style)
            if clip is not None:
                clips.append(clip)
        
        # End card (always slideshow style)
        logger.info("Creating end card...")
        end_clip = self.slideshow_gen._create_end_card()
        clips.append(end_clip)
        
        # Step 3: Concatenate all clips
        logger.info("\n--- Combining Video ---")
        final_video = concatenate_videoclips(clips, method='compose')
        
        # Add full audio track
        full_audio_path = os.path.join(
            self.config.get('output', {}).get('temp_directory', 'temp'),
            'full_voiceover.mp3'
        )
        
        if os.path.exists(full_audio_path):
            logger.info("Adding audio track...")
            audio = AudioFileClip(full_audio_path)
            final_video = final_video.set_audio(audio)
        
        # Step 4: Write video file
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
        
        logger.info(f"✓ Combined-style video generated successfully: {output_path}")
        return output_path
    
    def _assign_styles_to_segments(self, script_data: Dict) -> Dict:
        """
        Use AI to assign the best style to each segment.
        
        Args:
            script_data: Script data with segments
            
        Returns:
            Script data with style assignments added
        """
        if not self.client:
            # Fallback: alternate between styles
            logger.warning("Using default style rotation (no AI analysis)")
            return self._assign_styles_default(script_data)
        
        result = script_data.copy()
        
        for i, segment in enumerate(result['segments'], 1):
            style_choice = self._select_style_for_segment(segment, i)
            segment['selected_style'] = style_choice['style']
            segment['style_reason'] = style_choice['reason']
        
        return result
    
    def _select_style_for_segment(self, segment: Dict, segment_num: int) -> Dict:
        """
        Use GPT-4 to select the best style for a segment.
        
        Args:
            segment: Segment data
            segment_num: Segment number
            
        Returns:
            Dictionary with style and reason
        """
        # Create analysis prompt
        prompt = self._create_style_selection_prompt(segment, segment_num)
        
        try:
            # load system prompt from template
            system_template = self.jinja_env.get_template('style_selection_system.j2')
            system_prompt = system_template.render()
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content
            return self._parse_style_selection(result_text)
            
        except Exception as e:
            logger.error(f"Error selecting style for segment {segment_num}: {str(e)}")
            # Fallback
            return {
                'style': 'slideshow',
                'reason': 'Default fallback due to API error'
            }
    
    def _create_style_selection_prompt(self, segment: Dict, segment_num: int) -> str:
        """Create prompt for style selection."""
        
        # load and render template
        template = self.jinja_env.get_template('style_selection_prompt.j2')
        prompt = template.render(
            segment=segment,
            segment_num=segment_num
        )
        
        return prompt
    
    def _parse_style_selection(self, response_text: str) -> Dict:
        """Parse AI response for style selection."""
        
        style = 'slideshow'  # default
        reason = 'Default selection'
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('STYLE:'):
                style_text = line.replace('STYLE:', '').strip().lower()
                if 'slideshow' in style_text:
                    style = 'slideshow'
                elif 'animated' in style_text:
                    style = 'animated'
                elif 'ai' in style_text or 'generated' in style_text:
                    style = 'ai_generated'
            elif line.startswith('REASON:'):
                reason = line.replace('REASON:', '').strip()
        
        return {
            'style': style,
            'reason': reason
        }
    
    def _assign_styles_default(self, script_data: Dict) -> Dict:
        """
        Fallback style assignment without AI.
        Rotates through styles intelligently based on segment position.
        
        Args:
            script_data: Script data
            
        Returns:
            Script data with styles assigned
        """
        result = script_data.copy()
        
        # Pattern: Start with slideshow, then alternate animated and ai_generated
        # This creates visual variety
        style_pattern = ['slideshow', 'animated', 'ai_generated']
        
        for i, segment in enumerate(result['segments']):
            # Use pattern cycling
            style_index = i % len(style_pattern)
            style = style_pattern[style_index]
            
            # Override for first and last (always slideshow for consistency)
            if i == 0:
                style = 'slideshow'
                reason = 'Introduction works best with clean slideshow style'
            elif i == len(result['segments']) - 1:
                style = 'slideshow'
                reason = 'Conclusion works best with clean slideshow style'
            else:
                if style == 'animated':
                    reason = 'Dynamic content benefits from animations'
                elif style == 'ai_generated':
                    reason = 'Abstract concepts enhanced by custom visuals'
                else:
                    reason = 'Clear presentation with slideshow format'
            
            segment['selected_style'] = style
            segment['style_reason'] = reason
        
        return result
    
    def _generate_segment_with_style(self, segment: Dict, segment_num: int, 
                                     style: str) -> Optional[object]:
        """
        Generate a segment using the specified style.
        
        Args:
            segment: Segment data
            segment_num: Segment number
            style: Style to use ('slideshow', 'animated', 'ai_generated')
            
        Returns:
            Video clip or None
        """
        try:
            if style == 'slideshow':
                return self.slideshow_gen._create_segment_clip(segment, segment_num)
            elif style == 'animated':
                return self.animated_gen._create_animated_segment(segment, segment_num)
            elif style == 'ai_generated':
                return self.ai_gen._create_segment_clip(segment, segment_num)
            else:
                logger.warning(f"Unknown style '{style}', using slideshow")
                return self.slideshow_gen._create_segment_clip(segment, segment_num)
                
        except Exception as e:
            logger.error(f"Error generating segment {segment_num} with style {style}: {str(e)}")
            # Fallback to slideshow
            logger.info(f"Falling back to slideshow for segment {segment_num}")
            try:
                return self.slideshow_gen._create_segment_clip(segment, segment_num)
            except:
                return None


def generate_combined_video(script_with_audio: Dict, config: Dict, 
                            output_path: str) -> str:
    """
    Convenience function to generate combined-style video.
    
    Args:
        script_with_audio: Script data with audio
        config: Configuration dictionary
        output_path: Output video path
        
    Returns:
        Path to generated video
    """
    generator = CombinedGenerator(config)
    return generator.generate_video(script_with_audio, output_path)


if __name__ == "__main__":
    # Test the generator
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python combined.py <script_with_audio.json> [output.mp4]")
        print("\nFirst run Phases 1-4 to generate the script and audio:")
        print("  python script.py document.pdf --test-script")
        print("\nThe combined style uses AI to select the best visual approach")
        print("for each segment, mixing slideshow, animated, and AI-generated styles.")
        sys.exit(1)
    
    script_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output/combined_video.mp4"
    
    # Load script data
    print(f"\n=== Loading Script Data ===")
    with open(script_path, 'r') as f:
        script_data = json.load(f)
    
    print(f"Loaded script with {len(script_data['segments'])} segments")
    
    # Load config
    from core.config_loader import get_config
    config = get_config()
    
    # Generate video
    print(f"\n=== Generating Combined-Style Video ===\n")
    print("AI will analyze each segment and select the optimal visual style.")
    print("This creates the most dynamic and engaging result!\n")
    
    video_path = generate_combined_video(script_data, config.config, output_path)
    
    print(f"\n{'='*80}")
    print(f"✓ Combined-style video generated!")
    print(f"Output: {video_path}")
    print(f"{'='*80}\n")

