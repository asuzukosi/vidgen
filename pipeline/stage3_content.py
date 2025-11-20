"""
Stage 3: Content Analysis
Analyze content and create video outline.
Requires pipeline_id to load cached PipelineData.
"""

import sys
import os
import argparse
from typing import Optional
from pathlib import Path

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.context_processor import ContextProcessor
from core.content_analyzer import ContentAnalyzer
from core.stock_image_fetcher import StockImageFetcher
from core.image_generator import ImageGenerator
from core.pipeline_data import PipelineData

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def create_video_outline(pdf_path: str,
                         pipeline_id: str,
                         skip_stock: bool = False,
                         target_segments: int = 7,
                         segment_duration: int = 45) -> PipelineData:
    """
    Analyze content and create video outline.
    Requires pipeline_id to load cached PipelineData.
    
    Args:
        pdf_path: Path to PDF file
        pipeline_id: UUID of existing pipeline data
        skip_stock: Skip stock image fetching
        target_segments: Target number of video segments
        segment_duration: Target duration per segment in seconds
    
    Returns:
        PipelineData instance with video outline
    """
    logger.info("=== Stage 3: Content Analysis ===")
    
    config = get_config()
    temp_dir = config.get('output.temp_directory', 'temp')
    
    # Load pipeline data by ID (cache is compulsory)
    try:
        pipeline_data = PipelineData.load_by_id(pipeline_id, temp_dir)
        logger.info(f"Loaded pipeline data: {pipeline_data.id}")
    except FileNotFoundError:
        logger.error(f"Pipeline data not found for ID: {pipeline_id}")
        logger.error("Run stage1_parsing.py and stage2_images.py first")
        sys.exit(1)
    
    pipeline_data.update_stage("content_analysis", "in_progress")
    
    if not config.openai_api_key:
        logger.error("OpenAI API key required")
        pipeline_data.update_stage("content_analysis", "failed")
        return pipeline_data
    
    if not pipeline_data.parsed_content:
        logger.error("Parsed content not found in pipeline data")
        pipeline_data.update_stage("content_analysis", "failed")
        return pipeline_data
    
    try:
        pdf_content = pipeline_data.parsed_content
        images_metadata = pipeline_data.images_metadata or []
        
        logger.info(f"Loaded {len(pdf_content['sections'])} sections and {len(images_metadata)} images")
        
        # Process context into chunks
        logger.info("Processing context into chunks")
        all_content = ""
        for section in pdf_content['sections']:
            all_content += section['content']
        
        prompts_dir = config.get_prompts_directory()
        chunk_length = config.get('content.chunk_length', 4000)
        context_processor = ContextProcessor(
            all_content,
            config.openai_api_key,
            pdf_content['title'],
            chunk_length=chunk_length,
            split_by='\n',
            prompts_dir=prompts_dir
        )
        chunks = context_processor.get_chunks()
        pipeline_data.chunks = chunks
        
        # Store context processor information
        pipeline_data.context_processor_info = {
            'document_title': pdf_content['title'],
            'chunk_length': chunk_length,
            'split_by': '\n',
            'total_chunks': len(chunks),
            'total_content_length': len(all_content)
        }
        
        logger.info(f"Generated {len(chunks)} chunks")
        
        # Create video outline
        logger.info("Creating video outline")
        analyzer = ContentAnalyzer(
            api_key=config.openai_api_key,
            target_segments=target_segments,
            segment_duration=segment_duration,
            prompts_dir=prompts_dir
        )
        outline = analyzer.analyze_content(
            chunks=chunks,
            images_metadata=images_metadata,
            document_title=pdf_content['title']
        )
        
        # Fetch stock images
        if not skip_stock and config.get('images.use_stock_images', True):
            logger.info("Fetching stock images")
            fetcher = StockImageFetcher(config.unsplash_access_key, config.pexels_api_key)
            availability = fetcher.is_available()
            if availability['unsplash'] or availability['pexels']:
                preferred = config.get('images.preferred_stock_provider', 'unsplash')
                outline['segments'] = fetcher.fetch_for_segments(outline['segments'], preferred)
            else:
                logger.info("No stock image API keys configured")
        else:
            logger.info("Skipping stock images")
        
        # Generate AI images if enabled
        if config.get('images.use_ai_generated', False):
            logger.info("Generating AI images")
            generator = ImageGenerator(
                api_key=config.openai_api_key,
                model=config.get('images.ai_generator.model', 'dall-e-3'),
                quality=config.get('images.ai_generator.quality', 'standard'),
                size=config.get('images.ai_generator.size', '1024x1024'),
                output_dir=os.path.join(temp_dir, pipeline_data.id, 'ai_images'),
                prompts_dir=config.get_prompts_directory()
            )
            if generator.is_available():
                outline['segments'] = generator.generate_for_segments(
                    outline['segments'],
                    pipeline_id=pipeline_data.id
                )
            else:
                logger.warning("AI image generation not available (missing API key)")
        else:
            logger.info("Skipping AI image generation")
        
        # Update pipeline data
        pipeline_data.video_outline = outline
        pipeline_data.update_stage("content_analysis", "completed")
        
        # Save pipeline data
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"Video outline created. Pipeline ID: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"Error during content analysis: {str(e)}", exc_info=True)
        pipeline_data.update_stage("content_analysis", "failed")
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='Create video outline from PDF')
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='UUID of pipeline data (from stage1)')
    parser.add_argument('--skip-stock', action='store_true', help='Skip stock image fetching')
    parser.add_argument('--target-segments', type=int, default=7, help='Target number of video segments')
    parser.add_argument('--segment-duration', type=int, default=45, help='Target duration per segment in seconds')
    args = parser.parse_args()
    
    pipeline_data = create_video_outline(
        args.pdf_path,
        args.pipeline_id,
        skip_stock=args.skip_stock,
        target_segments=args.target_segments,
        segment_duration=args.segment_duration
    )
    
    if pipeline_data.status == "completed":
        logger.info(f"✓ Video outline created successfully. Pipeline ID: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"✗ Video outline creation failed. Pipeline ID: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
