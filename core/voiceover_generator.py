"""
voiceover generator module
generates audio voiceovers from scripts using elevenlabs or gtts.
handles audio file creation and timing metadata.
"""

import os
import json
from typing import Dict, Optional, Tuple
from pathlib import Path
from core.logger import get_logger
from pydub import AudioSegment


logger = get_logger(__name__)


class VoiceoverGenerator:
    """generate voiceover audio from scripts."""
    
    def __init__(self, provider: str = "elevenlabs", 
                 api_key: Optional[str] = None,
                 voice_id: Optional[str] = None,
                 output_dir: str = "temp/audio"):
        """
        initialize voiceover generator.
        args:
            provider: "elevenlabs" or "gtts"
            api_key: elevenlabs api key (if using elevenlabs)
            voice_id: elevenlabs voice id
            output_dir: directory to save audio files
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = voice_id or os.getenv('VOICE_ID', '21m00Tcm4TlvDq8ikWAM')
        self.output_dir = output_dir
        
        # create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # always initialize gtts as fallback
        self._init_gtts()
        
        # initialize provider
        if self.provider == "elevenlabs":
            if not self.api_key:
                logger.warning("elevenlabs api key not found. falling back to gtts.")
                self.provider = "gtts"
            else:
                self._init_elevenlabs()
    
    def _init_elevenlabs(self):
        """initialize elevenlabs client."""
        try:
            from elevenlabs import ElevenLabs, VoiceSettings
            self.client = ElevenLabs(api_key=self.api_key)
            self.voice_settings = VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
            logger.info("initialized elevenlabs voiceover generator")
        except ImportError:
            logger.error("elevenlabs package not installed. install with: pip install elevenlabs")
            self.provider = "gtts"
        except Exception as e:
            logger.error(f"error initializing elevenlabs: {str(e)}")
            self.provider = "gtts"
    
    def _init_gtts(self):
        """initialize gtts."""
        try:
            from gtts import gTTS
            self.gtts_class = gTTS
            logger.info("initialized gtts voiceover generator (free fallback)")
        except ImportError:
            logger.error("gtts package not installed. install with: pip install gtts")
            raise
    
    def generate_voiceovers(self, script_data: Dict) -> Dict:
        """
        generate voiceover audio for all segments.
        args:
            script_data: script data with segments
        returns:
            updated script data with audio file paths and metadata
        """
        logger.info(f"generating voiceovers for {len(script_data['segments'])} segments using {self.provider}")
        
        segments_with_audio = []
        
        for i, segment in enumerate(script_data['segments'], 1):
            logger.info(f"generating audio for segment {i}: {segment['title']}")
            
            script_text = segment.get('script', '')
            if not script_text:
                logger.warning(f"no script found for segment {i}")
                segments_with_audio.append(segment)
                continue
            
            # generate audio
            audio_path, duration = self._generate_segment_audio(script_text, i, segment['title'])
            
            # update segment with audio info
            segment_with_audio = segment.copy()
            segment_with_audio['audio_file'] = audio_path
            segment_with_audio['audio_duration'] = duration
            segment_with_audio['voiceover_provider'] = self.provider
            
            segments_with_audio.append(segment_with_audio)
        
        result = script_data.copy()
        result['segments'] = segments_with_audio
        result['total_audio_duration'] = sum(s.get('audio_duration', 0) for s in segments_with_audio)
        
        logger.info(f"Generated {len(segments_with_audio)} voiceovers, total duration: {result['total_audio_duration']:.1f}s")
        
        return result
    
    def _generate_segment_audio(self, text: str, segment_num: int, title: str) -> Tuple[str, float]:
        """
        generate audio for a single segment.
        args:
            text: script text
            segment_num: segment number
            title: segment title
        returns:
            tuple of (audio_file_path, duration_seconds)
        """
        # create filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:30]
        filename = f"segment_{segment_num:02d}_{safe_title}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        if self.provider == "elevenlabs":
            duration = self._generate_elevenlabs_audio(text, filepath)
        else:
            duration = self._generate_gtts_audio(text, filepath)
        
        logger.info(f"Generated audio: {filename} ({duration:.1f}s)")
        return filepath, duration
    
    def _generate_elevenlabs_audio(self, text: str, output_path: str) -> float:
        """
        generate audio using elevenlabs.
        args:
            text: text to convert to speech
            output_path: path to save audio file
        returns:
            duration in seconds
        """
        try:
            from elevenlabs import save
            
            # generate audio
            # using eleven_turbo_v2_5 which is available on free tier
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",
                voice_settings=self.voice_settings
            )
            save(audio_generator, output_path)
            # calculate duration (approximate: 150 words per minute)
            word_count = len(text.split())
            duration = (word_count / 150.0) * 60.0
            # get actual duration if available
            audio = AudioSegment.from_mp3(output_path)
            duration = len(audio) / 1000.0
            return duration
            
        except Exception as e:
            logger.error(f"Error generating ElevenLabs audio: {str(e)}")
            # Fallback to gTTS
            logger.info("Falling back to gTTS for this segment")
            return self._generate_gtts_audio(text, output_path)
    
    def _generate_gtts_audio(self, text: str, output_path: str) -> float:
        """
        generate audio using gtts (free fallback).
        args:
            text: text to convert to speech
            output_path: path to save audio file
        returns:
            duration in seconds
        """
        try:
            tts = self.gtts_class(text=text, lang='en', slow=False)
            tts.save(output_path)
            
            # Calculate duration
            word_count = len(text.split())
            duration = (word_count / 150.0) * 60.0  # Approximate
            
            # Get actual duration if available
            audio = AudioSegment.from_mp3(output_path)
            duration = len(audio) / 1000.0
            
            return duration
            
        except Exception as e:
            logger.error(f"Error generating gTTS audio: {str(e)}")
            raise
    
    def generate_full_audio(self, script_data: Dict, output_path: str) -> float:
        """
        generate a single audio file combining all segments.
        args:
            script_data: script data with audio files
            output_path: path to save combined audio
        returns:
            total duration in seconds
        """
        logger.info("**** combining all segments into single audio file ****")
            
        combined = AudioSegment.empty()
        for segment in script_data['segments']:
            audio_file = segment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio = AudioSegment.from_mp3(audio_file)
                combined += audio
                silence = AudioSegment.silent(duration=500)
                combined += silence
        combined.export(output_path, format="mp3")
        duration = len(combined) / 1000.0
        logger.info(f"Created combined audio: {output_path} ({duration:.1f}s)")
        return duration
    
    def save_metadata(self, script_data_with_audio: Dict, output_path: str):
        """
        save script data with audio metadata.
        args:
            script_data_with_audio: script data with audio info
            output_path: path to save JSON
        """
        with open(output_path, 'w') as f:
            json.dump(script_data_with_audio, f, indent=2)
        
        logger.info(f"Saved audio metadata to {output_path}")


def generate_voiceovers(script_data: Dict, provider: str = "elevenlabs") -> Dict:
    """
    convenience function to generate voiceovers.
    args:
        script_data: script data dictionary
        provider: "elevenlabs" or "gtts"
    returns:
        script data with audio files
    """
    generator = VoiceoverGenerator(provider)
    return generator.generate_voiceovers(script_data)


if __name__ == "__main__":
    # test the generator
    import sys
    
    if len(sys.argv) < 2:
        print("usage: python voiceover_generator.py <video_script.json> [provider]")
        print("provider: elevenlabs (default) or gtts")
        sys.exit(1)
    
    script_path = sys.argv[1]
    provider = sys.argv[2] if len(sys.argv) > 2 else "elevenlabs"
    
    print(f"**** loading script ****")
    with open(script_path, 'r') as f:
        script_data = json.load(f)
    
    print(f"loaded script with {len(script_data['segments'])} segments\n")
    
    print(f"**** generating voiceovers with {provider.upper()} ****\n")
    
    generator = VoiceoverGenerator(provider)
    result = generator.generate_voiceovers(script_data)
    
    print(f"**** voiceover generation complete ****")
    print(f"total segments: {len(result['segments'])}")
    print(f"total duration: {result.get('total_audio_duration', 0):.1f}s")
    print(f"**** segment audio files ****")
    
    for i, segment in enumerate(result['segments'], 1):
        audio_file = segment.get('audio_file', 'N/A')
        duration = segment.get('audio_duration', 0)
        print(f"  {i}. {segment['title']}: {os.path.basename(audio_file) if audio_file != 'N/A' else 'N/A'} ({duration:.1f}s)")
    
    # save metadata
    output_path = "temp/script_with_audio.json"
    generator.save_metadata(result, output_path)
    
    # try to create combined audio
    combined_path = "temp/full_voiceover.mp3"
    total_duration = generator.generate_full_audio(result, combined_path)
    if total_duration > 0:
        print(f"combined audio: {combined_path} ({total_duration:.1f}s)")
    
    print(f"audio metadata saved to: {output_path}")

