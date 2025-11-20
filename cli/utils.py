"""
cli utilities - helper functions for the cli application
"""

import os
import json
from pathlib import Path
from typing import Optional

from utils.logger import get_logger
from utils.config_loader import Config
from core.processors.pdf_processor import PDFProcessor
from core.pipeline_data import PipelineData

logger = get_logger(__name__)


def parse_document(pdf_path: str, pipeline_data: Optional[PipelineData] = None) -> PipelineData:
    """
    Parse document and extract structured content.
    
    Args:
        pdf_path: Path to PDF file
        pipeline_data: Existing pipeline data (optional)
        
    Returns:
        PipelineData instance with parsed content
    """
    logger.info("=== Parse Document ===")
    
    if pipeline_data is None:
        pipeline_data = PipelineData()
        pipeline_data.source_path = pdf_path
        pipeline_data.source_type = 'pdf'
    
    pipeline_data.update_stage("document_processing", "in_progress")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        pipeline_data.update_stage("document_processing", "failed")
        return pipeline_data
    
    try:
        from utils.config_loader import get_config
        config = get_config()
        temp_dir = config.get('output.temp_directory', 'temp')
        
        with PDFProcessor(pdf_path) as processor:
            content = processor.extract_structured_content()
            pipeline_data.parsed_content = content
            
            logger.info(f"PDF Title: {content['title']}")
            logger.info(f"Total Pages: {content['total_pages']}")
            logger.info(f"Sections Found: {len(content['sections'])}")
            
            pipeline_data.update_stage("document_processing", "completed")
            pipeline_data.save_to_folder(temp_dir)
            
            return pipeline_data
            
    except Exception as e:
        logger.error(f"Error during document parsing: {str(e)}", exc_info=True)
        pipeline_data.update_stage("document_processing", "failed")
        return pipeline_data


def extract_images(pdf_path: str, pipeline_data: Optional[PipelineData] = None) -> PipelineData:
    """
    Extract images from document and label them with AI.
    
    Args:
        pdf_path: Path to PDF file
        pipeline_data: Existing pipeline data (required - must have pipeline_id)
        
    Returns:
        PipelineData instance with extracted images
    """
    logger.info("=== Extract Images ===")
    
    if pipeline_data is None:
        logger.error("Pipeline data is required. Run parse_document first.")
        raise ValueError("Pipeline data is required for image extraction")
    
    from utils.config_loader import get_config
    from pipeline.stage2_images import extract_images as stage2_extract_images
    
    config = get_config()
    
    if not config.openai_api_key:
        logger.error("OpenAI API key not found. Image labeling requires OPENAI_API_KEY.")
        pipeline_data.update_stage("image_processing", "failed")
        return pipeline_data
    
    try:
        # Use stage2_images function which requires pipeline_id
        pipeline_data = stage2_extract_images(pdf_path, pipeline_data.id)
        return pipeline_data
            
    except Exception as e:
        logger.error(f"Error during image extraction: {str(e)}", exc_info=True)
        pipeline_data.update_stage("image_processing", "failed")
        return pipeline_data


def analyze_content(pdf_path: str, pipeline_data: Optional[PipelineData] = None) -> PipelineData:
    """
    Analyze content and create video outline.
    
    Args:
        pdf_path: Path to PDF file
        pipeline_data: Existing pipeline data (required - must have pipeline_id)
        
    Returns:
        PipelineData instance with video outline
    """
    logger.info("=== Analyze Content ===")
    
    if pipeline_data is None:
        logger.error("Pipeline data is required. Run parse_document first.")
        raise ValueError("Pipeline data is required for content analysis")
    
    from utils.config_loader import get_config
    from pipeline.stage3_content import create_video_outline
    
    config = get_config()
    
    if not config.openai_api_key:
        logger.error("OpenAI API key not found. Content analysis requires OPENAI_API_KEY.")
        pipeline_data.update_stage("content_analysis", "failed")
        return pipeline_data
    
    try:
        # Use stage3_content function which requires pipeline_id
        pipeline_data = create_video_outline(
            pdf_path,
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
    Generate scripts and voiceovers from video outline.
    
    Args:
        pipeline_data: Existing pipeline data (required - must have pipeline_id)
        
    Returns:
        PipelineData instance with scripts and audio
    """
    logger.info("=== Generate Script ===")
    
    if pipeline_data is None:
        logger.error("Pipeline data is required. Run previous stages first.")
        raise ValueError("Pipeline data is required for script generation")
    
    from utils.config_loader import get_config
    from pipeline.stage4_script import generate_scripts_and_voiceovers
    
    config = get_config()
    
    if not pipeline_data.video_outline:
        logger.error("Video outline not found. Run analyze_content first.")
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
        logger.error(f"Error during script generation: {str(e)}", exc_info=True)
        pipeline_data.update_stage("script_generation", "failed")
        return pipeline_data


def generate_full_video(
    pdf_path: str,
    output_path: str,
    config: 'Config'
) -> PipelineData:
    """
    Run complete pipeline to generate video from PDF.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Output video path
        config: Configuration object
    
    Returns:
        PipelineData instance with complete pipeline data
    """
    logger.info(f"=== Full Pipeline: PDF to Video ===")
    logger.info(f"Input: {pdf_path}")
    logger.info(f"Output: {output_path}\n")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        pipeline_data = PipelineData()
        pipeline_data.update_stage("initialization", "failed")
        return pipeline_data
    
    if not config.openai_api_key:
        logger.error("OpenAI API key required for video generation")
        pipeline_data = PipelineData()
        pipeline_data.update_stage("initialization", "failed")
        return pipeline_data
    
    try:
        temp_dir = config.get('output.temp_directory', 'temp')
        
        # Initialize pipeline data
        pipeline_data = PipelineData()
        pipeline_data.source_path = pdf_path
        pipeline_data.source_type = 'pdf'
        pipeline_data.config = {
            'target_segments': config.get('content.target_segments', 7),
            'segment_duration': config.get('content.segment_duration', 45),
            'voiceover_provider': config.get('voiceover.provider', 'elevenlabs')
        }
        pipeline_data.update_stage("document_processing", "in_progress")
        
        logger.info(f"Pipeline ID: {pipeline_data.id}\n")
        
        # Stage 1: Parse Document
        logger.info("--- Stage 1: Document Parsing ---")
        from pipeline.stage1_parsing import parse_document
        pipeline_data = parse_document(pdf_path, pipeline_data)
        if pipeline_data.status != "completed":
            return pipeline_data
        
        # Stage 2: Extract Images
        logger.info("--- Stage 2: Image Extraction ---")
        from pipeline.stage2_images import extract_images as stage2_extract_images
        pipeline_data = stage2_extract_images(pdf_path, pipeline_data.id)
        if pipeline_data.status != "completed":
            return pipeline_data
        
        # Stage 3: Analyze Content
        logger.info("--- Stage 3: Content Analysis ---")
        from pipeline.stage3_content import create_video_outline
        pipeline_data = create_video_outline(
            pdf_path,
            pipeline_data.id,
            skip_stock=False,
            target_segments=config.get('content.target_segments', 7),
            segment_duration=config.get('content.segment_duration', 45)
        )
        if pipeline_data.status != "completed":
            return pipeline_data
        
        # Stage 4: Generate Script
        logger.info("--- Stage 4: Script Generation ---")
        from pipeline.stage4_script import generate_scripts_and_voiceovers
        pipeline_data = generate_scripts_and_voiceovers(
            pipeline_data.id,
            provider=config.get('voiceover.provider', 'elevenlabs')
        )
        if pipeline_data.status != "completed":
            return pipeline_data
        
        # Stage 5: Generate Video
        logger.info("--- Stage 5: Video Generation ---")
        from pipeline.stage5_video import video_generation
        
        # Use provided output_path or let stage5 determine it using pipeline ID
        pipeline_data = video_generation(pipeline_data.id, output_path=output_path)
        
        logger.info(f"\n{'='*80}")
        logger.info("VIDEO GENERATION COMPLETE!")
        logger.info(f"{'='*80}")
        logger.info(f"Output: {pipeline_data.video_path}")
        logger.info(f"Pipeline ID: {pipeline_data.id}")
        
        # Display timing information
        if pipeline_data.stage_timings:
            logger.info(f"\nStage Timings:")
            for stage, timing in pipeline_data.stage_timings.items():
                if 'duration' in timing:
                    logger.info(f"  {stage}: {timing['duration']:.2f}s")
        
        logger.info(f"{'='*80}\n")
        
        return pipeline_data
        
    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}", exc_info=True)
        if 'pipeline_data' in locals():
            pipeline_data.update_stage(pipeline_data.current_stage, "failed")
            pipeline_data.save_to_folder(temp_dir)
        else:
            pipeline_data = PipelineData()
            pipeline_data.update_stage("initialization", "failed")
        return pipeline_data

