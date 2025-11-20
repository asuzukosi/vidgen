"""
Stage 2: Image Extraction and Labeling
Extract images from PDF and label them with AI.
Requires pipeline_id to load cached PipelineData.
"""

import sys
import os
import argparse
from pathlib import Path

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.processors.pdf_processor import PDFProcessor
from core.image_labeler import ImageLabeler
from core.pipeline_data import PipelineData

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def extract_images(pdf_path: str, pipeline_id: str) -> PipelineData:
    """
    Extract images from PDF and label them with AI.
    Requires pipeline_id to load cached PipelineData.
    
    Args:
        pdf_path: Path to PDF file
        pipeline_id: UUID of existing pipeline data
    
    Returns:
        PipelineData instance with extracted and labeled images
    """
    logger.info("=== Stage 2: Image Extraction and Labeling ===")
    
    config = get_config()
    temp_dir = config.get('output.temp_directory', 'temp')
    
    # Load pipeline data by ID (cache is compulsory)
    try:
        pipeline_data = PipelineData.load_by_id(pipeline_id, temp_dir)
        logger.info(f"Loaded pipeline data: {pipeline_data.id}")
    except FileNotFoundError:
        logger.error(f"Pipeline data not found for ID: {pipeline_id}")
        logger.error("Run stage1_parsing.py first to create pipeline data")
        sys.exit(1)
    
    pipeline_data.update_stage("image_processing", "in_progress")
    
    if not config.openai_api_key:
        logger.error("OpenAI API key required for image labeling")
        pipeline_data.update_stage("image_processing", "failed")
        return pipeline_data
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        pipeline_data.update_stage("image_processing", "failed")
        return pipeline_data
    
    try:
        images_dir = os.path.join(temp_dir, pipeline_data.id, 'images')
        Path(images_dir).mkdir(parents=True, exist_ok=True)
        
        # Extract images
        logger.info("Extracting images from PDF")
        with PDFProcessor(pdf_path, images_dir) as processor:
            images_metadata = processor.extract_images()
            
            if not images_metadata:
                logger.info("No images found in PDF")
                pipeline_data.images_metadata = []
                pipeline_data.update_stage("image_processing", "completed")
                pipeline_data.save_to_folder(temp_dir)
                return pipeline_data
            
            stats = processor.get_image_stats()
            logger.info(f"Extracted {stats['total_images']} images")
            
            # Label images with AI
            logger.info("Labeling images with AI")
            labeler = ImageLabeler(config.openai_api_key, prompts_dir=config.get_prompts_directory())
            labeled_metadata = labeler.label_images_batch(images_metadata)
            
            metadata_path = os.path.join(images_dir, 'images_metadata_labeled.json')
            labeler.save_labeled_metadata(labeled_metadata, metadata_path)
            
            pipeline_data.images_metadata = labeled_metadata
        
        # Save pipeline data
        pipeline_data.update_stage("image_processing", "completed")
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"Image extraction complete. Pipeline ID: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"Error during image extraction: {str(e)}", exc_info=True)
        pipeline_data.update_stage("image_processing", "failed")
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='Extract images from PDF and label with AI')
    parser.add_argument('pdf_file', type=str, help='Path to the PDF file')
    parser.add_argument('--pipeline-id', type=str, required=True, 
                        help='UUID of pipeline data (from stage1)')
    args = parser.parse_args()
    
    pipeline_data = extract_images(args.pdf_file, args.pipeline_id)
    
    if pipeline_data.status == "completed":
        logger.info(f"✓ Image extraction successful. Pipeline ID: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"✗ Image extraction failed. Pipeline ID: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
