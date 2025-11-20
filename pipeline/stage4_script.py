"""
Stage 4: Script Generation and Voiceover
Generate scripts and voiceovers from video outline.
Requires pipeline_id to load cached PipelineData.
"""

import sys
import os
import argparse
from typing import Optional

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.script_generator import ScriptGenerator
from core.voiceover_generator import VoiceoverGenerator
from core.pipeline_data import PipelineData

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def generate_scripts_and_voiceovers(pipeline_id: str,
                                    provider: Optional[str] = None) -> PipelineData:
    """
    Generate scripts and voiceovers from video outline.
    Requires pipeline_id to load cached PipelineData.
    
    Args:
        pipeline_id: UUID of existing pipeline data
        provider: Voiceover provider (elevenlabs or gtts)
    
    Returns:
        PipelineData instance with scripts and audio
    """
    logger.info("=== Stage 4: Script Generation and Voiceover ===")
    
    config = get_config()
    temp_dir = config.get('output.temp_directory', 'temp')
    
    # Load pipeline data by ID (cache is compulsory)
    try:
        pipeline_data = PipelineData.load_by_id(pipeline_id, temp_dir)
        logger.info(f"Loaded pipeline data: {pipeline_data.id}")
    except FileNotFoundError:
        logger.error(f"Pipeline data not found for ID: {pipeline_id}")
        logger.error("Run previous stages first to create pipeline data")
        sys.exit(1)
    
    pipeline_data.update_stage("script_generation", "in_progress")
    
    if not pipeline_data.video_outline:
        logger.error("Video outline not found in pipeline data")
        logger.error("Run stage3_content.py first")
        pipeline_data.update_stage("script_generation", "failed")
        return pipeline_data
    
    try:
        outline = pipeline_data.video_outline
        logger.info(f"Using outline with {len(outline['segments'])} segments")
        
        # Generate scripts
        logger.info("Generating scripts")
        script_gen = ScriptGenerator(api_key=config.openai_api_key, prompts_dir=config.get_prompts_directory())
        script_data = script_gen.generate_script(outline)
        pipeline_data.script_data = script_data
        logger.info(f"Generated scripts for {len(script_data['segments'])} segments")
        
        # Generate voiceovers
        voiceover_provider = provider or config.get('voiceover.provider', 'elevenlabs')
        logger.info(f"Using voiceover provider: {voiceover_provider}")
        
        audio_dir = os.path.join(temp_dir, pipeline_data.id, 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        voiceover_gen = VoiceoverGenerator(
            provider=voiceover_provider,
            api_key=config.elevenlabs_api_key,
            voice_id=config.get('voiceover.voice_id'),
            output_dir=audio_dir
        )
        
        script_with_audio = voiceover_gen.generate_voiceovers(script_data)
        pipeline_data.script_with_audio = script_with_audio
        logger.info(f"Generated voiceovers for {len(script_with_audio['segments'])} segments")
        
        # Generate combined audio
        combined_audio_path = os.path.join(audio_dir, 'full_voiceover.mp3')
        total_duration = voiceover_gen.generate_full_audio(script_with_audio, combined_audio_path)
        logger.info(f"Combined audio generated: {combined_audio_path} ({total_duration:.1f}s)")
        
        # Save pipeline data
        pipeline_data.update_stage("script_generation", "completed")
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"Scripts and voiceovers generated. Pipeline ID: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"Error during script generation: {str(e)}", exc_info=True)
        pipeline_data.update_stage("script_generation", "failed")
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='Generate scripts and voiceovers')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='UUID of pipeline data (from previous stages)')
    parser.add_argument('--provider', type=str, choices=['elevenlabs', 'gtts'], default=None,
                        help='Voiceover provider: elevenlabs or gtts')
    args = parser.parse_args()
    
    pipeline_data = generate_scripts_and_voiceovers(
        args.pipeline_id,
        provider=args.provider
    )
    
    if pipeline_data.status == "completed":
        logger.info(f"✓ Scripts and voiceovers generated successfully. Pipeline ID: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"✗ Script generation failed. Pipeline ID: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
