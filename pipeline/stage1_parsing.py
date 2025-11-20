"""
Stage 1: Document Parsing
Extract and analyze the structure of a PDF document.
Creates initial PipelineData object.
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
from core.pipeline_data import PipelineData

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def parse_document(pdf_path: str, pipeline_data: PipelineData = None) -> PipelineData:
    """
    Parse document and extract structured content.
    Creates new PipelineData if not provided.
    
    Args:
        pdf_path: Path to PDF file
        pipeline_data: Optional existing pipeline data (creates new if None)
    
    Returns:
        PipelineData instance with parsed content
    """
    logger.info("=== Stage 1: Document Parsing ===")
    
    # Create new PipelineData if not provided
    if pipeline_data is None:
        pipeline_data = PipelineData()
        pipeline_data.source_path = pdf_path
        pipeline_data.source_type = 'pdf'
        logger.info(f"Created new pipeline with ID: {pipeline_data.id}")
    
    pipeline_data.update_stage("document_processing", "in_progress")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        pipeline_data.update_stage("document_processing", "failed")
        return pipeline_data
    
    try:
        config = get_config()
        temp_dir = config.get('output.temp_directory', 'temp')
        
        # Parse PDF
        logger.info(f"Parsing PDF: {pdf_path}")
        with PDFProcessor(pdf_path) as processor:
            content = processor.extract_structured_content()
            pipeline_data.parsed_content = content
        
        logger.info(f"Title: {content['title']}")
        logger.info(f"Total Pages: {content['total_pages']}")
        logger.info(f"Sections: {len(content['sections'])}")
        
        # Save pipeline data
        pipeline_data.update_stage("document_processing", "completed")
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"Document parsing complete. Pipeline ID: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"Error during document parsing: {str(e)}", exc_info=True)
        pipeline_data.update_stage("document_processing", "failed")
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='Parse a PDF file and extract structure')
    parser.add_argument('pdf_file', type=str, help='Path to the PDF file')
    args = parser.parse_args()
    
    pipeline_data = parse_document(args.pdf_file)
    
    if pipeline_data.status == "completed":
        logger.info(f"✓ Document parsing successful. Pipeline ID: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"✗ Document parsing failed. Pipeline ID: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
