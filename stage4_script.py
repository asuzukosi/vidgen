#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 4: SCRIPT GENERATION & VOICEOVER TEST

PURPOSE:
    Generate natural narration scripts and create voiceover audio:
    - Write conversational scripts for each segment
    - Generate professional voiceover audio
    - Calculate timing and duration metadata
    - Create combined audio track

APPROACH:
    1. Script Generation (GPT-4):
       - Creates natural, conversational narration
       - Matches target duration (150 words/minute speaking rate)
       - Maintains engaging tone and clarity
       - Connects segments into cohesive narrative
    
    2. Voiceover Generation (ElevenLabs or gTTS):
       - ElevenLabs (primary): High-quality, natural-sounding voices
       - gTTS (fallback): Free Google Text-to-Speech
       - Automatic fallback if ElevenLabs unavailable
       - Generates individual segment audio files
       - Creates combined full audio track

OUTPUT:
    - Scripts: temp/video_script.json, temp/video_script.txt
    - Audio files: temp/audio/segment_XX_<title>.mp3
    - Combined audio: temp/full_voiceover.mp3
    - Metadata: temp/script_with_audio.json

OPTIONS:
    --use-cached     Use previously generated outline
    --provider       Voiceover provider: elevenlabs or gtts

USAGE:
    python test_stage4_script.py <pdf_file> [options]
    
EXAMPLES:
    python test_stage4_script.py document.pdf
    python test_stage4_script.py document.pdf --use-cached
    python test_stage4_script.py document.pdf --provider gtts
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logging, get_logger
from core.config_loader import get_config
from core.script_generator import ScriptGenerator
from core.voiceover_generator import VoiceoverGenerator

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def test_script_and_voiceover(pdf_path: str, use_cached: bool = False, provider: str = None):
    """
    Test script generation and voiceover creation.
    
    Args:
        pdf_path: Path to PDF file
        use_cached: Use cached outline
        provider: Voiceover provider (elevenlabs or gtts)
    """
    print("\n" + "="*80)
    print("STAGE 4: SCRIPT GENERATION & VOICEOVER")
    print("="*80 + "\n")
    
    config = get_config()
    
    if not config.openai_api_key:
        print("❌ Error: OpenAI API key required")
        return False
    
    try:
        temp_dir = 'temp'
        outline_path = os.path.join(temp_dir, 'video_outline.json')
        
        # Load outline
        if not os.path.exists(outline_path):
            print("❌ Error: Video outline not found")
            print("Run test_stage3_content.py first")
            return False
        
        print("📦 Loading video outline...")
        with open(outline_path, 'r') as f:
            outline = json.load(f)
        print(f"✓ Loaded outline with {len(outline['segments'])} segments\n")
        
        # Step 1: Generate scripts
        print("="*80)
        print("STEP 1: GENERATING SCRIPTS WITH GPT-4")
        print("="*80 + "\n")
        
        script_gen = ScriptGenerator(config.openai_api_key)
        script_data = script_gen.generate_script(outline)
        
        # Save scripts
        script_path = os.path.join(temp_dir, 'video_script.json')
        text_path = os.path.join(temp_dir, 'video_script.txt')
        script_gen.save_script(script_data, script_path)
        script_gen.export_script_text(script_data, text_path)
        
        # Display scripts
        print("\n" + "="*80)
        print(f"GENERATED SCRIPTS: {script_data['title']}")
        print("="*80)
        total_words = sum(s['word_count'] for s in script_data['segments'])
        print(f"Total Segments: {script_data['total_segments']}")
        print(f"Total Words: {total_words}")
        print(f"Estimated Speaking Time: ~{total_words / 150:.1f} minutes")
        print("="*80)
        
        for i, segment in enumerate(script_data['segments'], 1):
            print(f"\n[{i}] {segment['title']}")
            print(f"    Duration: {segment['duration']}s")
            print(f"    Words: {segment['word_count']}")
            print(f"    Script Preview:")
            
            # Show first 150 characters
            preview = segment['script'][:150]
            if len(segment['script']) > 150:
                preview += "..."
            print(f"    \"{preview}\"")
        
        # Step 2: Generate voiceovers
        print("\n" + "="*80)
        print("STEP 2: GENERATING VOICEOVERS")
        print("="*80 + "\n")
        
        voiceover_provider = provider or config.get('voiceover.provider', 'elevenlabs')
        print(f"Using provider: {voiceover_provider}")
        
        voiceover_gen = VoiceoverGenerator(
            provider=voiceover_provider,
            api_key=config.elevenlabs_api_key,
            voice_id=config.get('voiceover.voice_id'),
            output_dir=os.path.join(temp_dir, 'audio')
        )
        
        result = voiceover_gen.generate_voiceovers(script_data)
        
        # Save result
        audio_metadata_path = os.path.join(temp_dir, 'script_with_audio.json')
        voiceover_gen.save_metadata(result, audio_metadata_path)
        
        # Create combined audio
        combined_audio_path = os.path.join(temp_dir, 'full_voiceover.mp3')
        total_duration = voiceover_gen.generate_full_audio(result, combined_audio_path)
        
        # Display results
        print("\n" + "="*80)
        print("VOICEOVER GENERATION COMPLETE")
        print("="*80)
        print(f"Total Segments: {len(result['segments'])}")
        print(f"Total Audio Duration: {result.get('total_audio_duration', 0):.1f}s (~{result.get('total_audio_duration', 0) / 60:.1f} min)")
        print(f"Provider: {voiceover_provider}")
        print("="*80)
        
        print("\nGenerated Audio Files:")
        for i, segment in enumerate(result['segments'], 1):
            audio_file = segment.get('audio_file')
            duration = segment.get('audio_duration', 0)
            if audio_file:
                print(f"  [{i}] {segment['title']}")
                print(f"      {os.path.basename(audio_file)} ({duration:.1f}s)")
        
        if total_duration > 0:
            print(f"\n✓ Combined audio: {combined_audio_path} ({total_duration:.1f}s)")
        
        print("\n" + "="*80)
        print("✅ STAGE 4 COMPLETE")
        print("="*80)
        print(f"Scripts saved to: {script_path}")
        print(f"Text script: {text_path}")
        print(f"Audio metadata: {audio_metadata_path}")
        print(f"Combined audio: {combined_audio_path}")
        print(f"\nNext step: python test_stage5_video.py {pdf_path} --style <style>")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during script/voiceover generation: {str(e)}")
        logger.error(f"Error: {str(e)}", exc_info=True)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_stage4_script.py <pdf_file> [options]")
        print("\nOptions:")
        print("  --use-cached     Use previously generated outline")
        print("  --provider NAME  Voiceover provider: elevenlabs or gtts")
        print("\nExamples:")
        print("  python test_stage4_script.py document.pdf")
        print("  python test_stage4_script.py document.pdf --use-cached")
        print("  python test_stage4_script.py document.pdf --provider gtts")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    use_cached = '--use-cached' in sys.argv
    
    provider = None
    if '--provider' in sys.argv:
        idx = sys.argv.index('--provider')
        if idx + 1 < len(sys.argv):
            provider = sys.argv[idx + 1]
    
    success = test_script_and_voiceover(pdf_path, use_cached, provider)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

