"""
cli utilities - helper functions for the cli application
"""

import os
from typing import Optional

from utils.logger import get_logger
from utils.config_loader import Config
from core.processors.pdf_processor import PDFProcessor
from core.pipeline_data import PipelineData

logger = get_logger('cli_utils')


def parse_document(pdf_path: str, extract_images: bool = True) -> PipelineData:
    """
    parse document, extract structured content, and optionally extract/label images.
    creates new pipeline data.
    
    args:
        pdf_path: path to the pdf file
        extract_images: whether to extract and label images (default: True)
    
    returns:
        pipeline data with parsed content and optionally labeled images
    """
    logger.info("document processing started")
    
    from pipeline.stage1_parsing import parse_document as stage1_parse
    return stage1_parse(pdf_path, extract_images=extract_images)


# extract_images function removed - now integrated into parse_document operation


def analyze_content(pipeline_data: Optional[PipelineData] = None) -> PipelineData:
    """
    analyze content and create video outline.
    args:
        pipeline_data: existing pipeline data (required - must have pipeline_id)
    returns:
        pipeline data with video outline
    """
    logger.info("content analysis started")
    
    if pipeline_data is None:
        logger.error("pipeline data is required. run parse_document first.")
        raise ValueError("pipeline data is required for content analysis")
    
    from utils.config_loader import get_config
    from pipeline.stage2_content import create_video_outline
    
    config = get_config()
    
    if not config.openai_api_key:
        logger.error("openai api key not found. content analysis requires openai api key.")
        pipeline_data.update_stage("content_analysis", "failed")
        return pipeline_data
    
    try:
        # use stage3_content function which requires pipeline_id
        pipeline_data = create_video_outline(
            pipeline_id=pipeline_data.id,
            skip_stock=False,
            target_segments=config.get('content.target_segments', 7),
            segment_duration=config.get('content.segment_duration', 45)
        )
        
        return pipeline_data
        
    except Exception as e:
        logger.error(f"Error during content analysis: {str(e)}", exc_info=True)
        pipeline_data.update_stage("content_analysis", "failed")
        return pipeline_data


def generate_script(pipeline_data: Optional[PipelineData] = None) -> PipelineData:
    """
    generate scripts and voiceovers from video outline.
    args:
        pipeline_data: existing pipeline data (required - must have pipeline_id)
    returns:
        pipeline data with scripts and audio
    """
    logger.info("script generation started")
    
    if pipeline_data is None:
        logger.error("pipeline data is required. run previous stages first.")
        raise ValueError("pipeline data is required for script generation")
    
    from utils.config_loader import get_config
    from pipeline.stage3_script import generate_scripts_and_voiceovers
    
    config = get_config()
    
    if not pipeline_data.video_outline:
        logger.error("video outline not found. run analyze_content first.")
        pipeline_data.update_stage("script_generation", "failed")
        return pipeline_data
    
    try:
        # Use stage4_script function which requires pipeline_id
        pipeline_data = generate_scripts_and_voiceovers(
            pipeline_id=pipeline_data.id,
            provider=config.get('voiceover.provider', 'elevenlabs')
        )
        
        return pipeline_data
        
    except Exception as e:
        logger.error(f"error during script generation: {str(e)}", exc_info=True)
        pipeline_data.update_stage("script_generation", "failed")
        return pipeline_data


def generate_full_video(
    pdf_path: str,
    output_path: str,
    config: 'Config'
) -> PipelineData:
    """
    run complete pipeline to generate video from PDF.
    args:
        pdf_path: path to the pdf file
        output_path: output video path
        config: configuration object
    returns:
        pipeline data with complete pipeline data
    """
    logger.info(f"full pipeline: pdf to video")
    logger.info(f"input: {pdf_path}")
    logger.info(f"output: {output_path}\n")
    
    if not os.path.exists(pdf_path):
        logger.error(f"pdf file not found: {pdf_path}")
        pipeline_data = PipelineData()
        pipeline_data.update_stage("initialization", "failed")
        return pipeline_data
    
    if not config.openai_api_key:
        logger.error("openai api key required for video generation")
        pipeline_data = PipelineData()
        pipeline_data.update_stage("initialization", "failed")
        return pipeline_data
    
    try:
        temp_dir = config.get('output.temp_directory', 'temp')
        
        # operation 1: document processing (includes image extraction and labeling)
        logger.info("operation 1: document processing")
        from pipeline.stage1_parsing import parse_document
        pipeline_data = parse_document(pdf_path, extract_images=True)
        
        # store configuration in pipeline data
        pipeline_data.config = {
            'target_segments': config.get('content.target_segments', 7),
            'segment_duration': config.get('content.segment_duration', 45),
            'voiceover_provider': config.get('voiceover.provider', 'elevenlabs')
        }
        
        logger.info(f"pipeline ID: {pipeline_data.id}\n")
        
        if pipeline_data.status != "completed":
            return pipeline_data
        
        # operation 2: content analysis
        logger.info("operation 2: content analysis")
        from pipeline.stage2_content import create_video_outline
        pipeline_data = create_video_outline(
            pipeline_id=pipeline_data.id,
            skip_stock=False,
            target_segments=config.get('content.target_segments', 7),
            segment_duration=config.get('content.segment_duration', 45)
        )
        if pipeline_data.status != "completed":
            return pipeline_data
        
        # operation 3: script generation
        logger.info("operation 3: script generation")
        from pipeline.stage3_script import generate_scripts_and_voiceovers
        pipeline_data = generate_scripts_and_voiceovers(
            pipeline_data.id,
            provider=config.get('voiceover.provider', 'elevenlabs')
        )
        if pipeline_data.status != "completed":
            return pipeline_data
        
        # operation 4: video generation
        logger.info("operation 4: video generation")
        from pipeline.stage4_video import video_generation
        
        # use provided output_path or let video generation determine it using pipeline ID
        pipeline_data = video_generation(pipeline_data.id, output_path=output_path)
        
        logger.info(f"\n{'='*80}")
        logger.info("video generation complete!")
        logger.info(f"{'='*80}")
        logger.info(f"Output: {pipeline_data.video_path}")
        logger.info(f"pipeline ID: {pipeline_data.id}")
        
        # Display timing information
        if pipeline_data.stage_timings:
            logger.info(f"\nstage timings:")
            for stage, timing in pipeline_data.stage_timings.items():
                if 'duration' in timing:
                    logger.info(f"  {stage}: {timing['duration']:.2f}s")
        
        logger.info(f"{'='*80}\n")
        
        return pipeline_data
        
    except Exception as e:
        logger.error(f"error during video generation: {str(e)}", exc_info=True)
        if 'pipeline_data' in locals():
            pipeline_data.update_stage(pipeline_data.current_stage, "failed")
            pipeline_data.save_to_folder(temp_dir)
        else:
            pipeline_data = PipelineData()
            pipeline_data.update_stage("initialization", "failed")
        return pipeline_data

