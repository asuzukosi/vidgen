"""
Stage 5: Video Generation
Generate video from script and audio.
Requires pipeline_id to load cached PipelineData.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.video_generator import VideoGenerator
from core.pipeline_data import PipelineData

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def video_generation(pipeline_id: str,
                     output_path: Optional[str] = None) -> PipelineData:
    """
    Generate video from script and audio.
    Requires pipeline_id to load cached PipelineData.
    
    Args:
        pipeline_id: UUID of existing pipeline data
        output_path: Custom output path for video
    
    Returns:
        PipelineData instance with video path
    """
    logger.info("=== Stage 5: Video Generation ===")
    
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
    
    pipeline_data.update_stage("video_generation", "in_progress")
    
    if not pipeline_data.script_with_audio:
        logger.error("Script with audio not found in pipeline data")
        logger.error("Run stage4_script.py first")
        pipeline_data.update_stage("video_generation", "failed")
        return pipeline_data
    
    try:
        script_with_audio = pipeline_data.script_with_audio
        logger.info(f"Using script with audio for {len(script_with_audio['segments'])} segments")
        
        # Determine output path (use pipeline ID for filename)
        if not output_path:
            output_dir = config.get('output.directory', 'output')
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_path = os.path.join(output_dir, f"video_{pipeline_data.id}.mp4")
        
        # Store output path in pipeline data
        pipeline_data.output_path = output_path
        
        logger.info(f"Generating video...")
        logger.info(f"Output: {output_path}")
        
        # Generate video
        video_gen = VideoGenerator(config)
        video_path = video_gen.generate_video(script_with_audio, output_path)
        
        if os.path.exists(video_path):
            pipeline_data.video_path = video_path
            pipeline_data.output_path = output_path  # Ensure it's stored
            pipeline_data.update_stage("video_generation", "completed")
            logger.info(f"Video generated successfully: {video_path}")
        else:
            logger.error("Video file was not created")
            pipeline_data.update_stage("video_generation", "failed")
            return pipeline_data
        
        # Save pipeline data
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"Video generation complete. Pipeline ID: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}", exc_info=True)
        pipeline_data.update_stage("video_generation", "failed")
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='Generate video from script and audio')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='UUID of pipeline data (from previous stages)')
    parser.add_argument('--output', type=str, default=None,
                        help='Custom output path for video')
    args = parser.parse_args()
    
    pipeline_data = video_generation(
        args.pipeline_id,
        output_path=args.output
    )
    
    if pipeline_data.status == "completed" and pipeline_data.video_path:
        logger.info(f"✓ Video generated successfully: {pipeline_data.video_path}")
        logger.info(f"Pipeline ID: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"✗ Video generation failed. Pipeline ID: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
