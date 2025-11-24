"""
document processing operation

parse pdf document, extract structured content, and label images with AI.
creates initial pipeline data object with all extracted content.

workflow sequence:
    this is typically the first operation in the standard workflow:
    1. document_processing  - parse pdf and extract content (THIS MODULE)
    2. content_analysis     - analyze content and create video outline
    3. script_generation    - generate narration scripts and voiceovers
    4. video_generation     - compose final video from all assets
    
    note: the workflow can be customized based on document type and requirements.
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
logger = get_logger('document_processing')


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
    
    # create new pipeline data
    pipeline_data = PipelineData()
    pipeline_data.source_path = pdf_path
    pipeline_data.source_type = 'pdf'
    logger.info(f"created new pipeline with id: {pipeline_data.id}")
    
    pipeline_data.update_stage("document_processing", "in_progress")
    
    if not os.path.exists(pdf_path):
        logger.error(f"pdf file not found: {pdf_path}")
        pipeline_data.update_stage("document_processing", "failed")
        return pipeline_data
    
    try:
        config = get_config()
        temp_dir = config.get('output.temp_directory', 'temp')
        images_dir = os.path.join(temp_dir, pipeline_data.id, 'images')
        
        # parsing pdf and extracting structured content
        logger.info(f"parsing pdf: {pdf_path}")
        with PDFProcessor(pdf_path, images_output_dir=images_dir) as processor:
            content = processor.extract_structured_content()
            pipeline_data.parsed_content = content
            
            # logging content info
            logger.info(f"title: {content['title']}")
            logger.info(f"total pages: {content['total_pages']}")
            logger.info(f"sections: {len(content['sections'])}")
            
            # extract and label images if requested
            if extract_images:
                logger.info("extracting images from pdf")
                images_metadata = processor.extract_images()
                
                if images_metadata:
                    stats = processor.get_image_stats()
                    logger.info(f"extracted {stats['total_images']} images")
                    
                    # label images with ai if api key is available
                    if config.openai_api_key:
                        logger.info("labeling images with AI")
                        try:
                            labeler = ImageLabeler(config.openai_api_key, 
                                                 prompts_dir=config.get_prompts_directory())
                            labeled_metadata = labeler.label_images_batch(images_metadata)
                            
                            # save labeled metadata
                            Path(images_dir).mkdir(parents=True, exist_ok=True)
                            metadata_path = os.path.join(images_dir, 'images_metadata_labeled.json')
                            labeler.save_labeled_metadata(labeled_metadata, metadata_path)
                            
                            pipeline_data.images_metadata = labeled_metadata
                            logger.info(f"labeled {len(labeled_metadata)} images")
                        except Exception as e:
                            logger.warning(f"image labeling failed: {str(e)}")
                            logger.warning("continuing without labeled images")
                            pipeline_data.images_metadata = images_metadata
                    else:
                        logger.warning("openai api key not found, skipping image labeling")
                        pipeline_data.images_metadata = images_metadata
                else:
                    logger.info("no images found in pdf")
                    pipeline_data.images_metadata = []
        
        # updating and saving pipeline data
        pipeline_data.update_stage("document_processing", "completed")
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"document processing complete. pipeline ID: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"error during document processing: {str(e)}", exc_info=True)
        pipeline_data.update_stage("document_processing", "failed")
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='parse pdf and extract content including images')
    parser.add_argument('pdf_file', type=str, help='path to the pdf file')
    parser.add_argument('--skip-images', action='store_true', 
                       help='skip image extraction and labeling')
    args = parser.parse_args()
    
    pipeline_data = parse_document(args.pdf_file, extract_images=not args.skip_images)

    if pipeline_data.status == "completed":
        logger.info(f"document processing successful. pipeline ID: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"document processing failed. pipeline ID: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
