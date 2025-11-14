#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image extraction & ai labeling test
extract images from pdf and use ai to label and describe them:
    - extract all images with sufficient quality
    - filter out decorative elements (icons, logos)
    - use gpt-4 vision to analyze each image
    - generate descriptive labels and metadata
use pymupdf library to:
    1. extract images with metadata (size, position, format)
    2. filters images by minimum dimensions (100x100px)
    3. use openai gpt-4 vision api to analyze each image to determine:
       - content type (diagram, chart, photo, screenshot, etc.)
       - main subject and key elements
       - relevance to document content    
    4. save labeled metadata for use in video segmentation
output:
    - extracted images: temp/images/
    - labeled metadata: temp/images/images_metadata_labeled.json
    - console output with image descriptions
options:
    --use-cached    Use previously extracted images (skip extraction)
usage:
    python stage2_images.py <pdf_file> [--use-cached]
example:
    python stage2_images.py document.pdf
    python stage2_images.py document.pdf --use-cached
"""

import sys
import os
import json
import argparse
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logging, get_logger
from core.config_loader import get_config
from core.image_extractor import ImageExtractor
from core.image_labeler import ImageLabeler

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def stage2_images(pdf_path: str, use_cached: bool = False):
    """
    test image extraction and ai labeling.
    args:
        pdf_path: path to pdf file
        use_cached: use cached extraction results
    returns:
        True if successful, False otherwise
    """
    logger.info("*"*80)
    logger.info("image extraction & ai labeling test")
    logger.info("*"*80)
    
    config = get_config()
    
    if not config.openai_api_key:
        logger.error("openai api key required for image labeling")
        logger.error("set OPENAI_API_KEY in your .env file")
        return False
    
    if not os.path.exists(pdf_path):
        logger.error(f"pdf file not found: {pdf_path}")
        return False
    
    try:
        images_dir = 'temp/images'
        metadata_path = os.path.join(images_dir, 'images_metadata_labeled.json')
        
        # check for cached results
        if use_cached and os.path.exists(metadata_path):
            logger.info("using cached image metadata...")
            with open(metadata_path, 'r') as f:
                labeled_metadata = json.load(f)
            logger.info(f"loaded {len(labeled_metadata)} labeled images\n")
        else:
            # step 1: extract images
            logger.info("*"*80)
            logger.info("step 1: extracting images")
            logger.info("*"*80)
            
            extractor = ImageExtractor(pdf_path, images_dir)
            images_metadata = extractor.extract_images()
            
            if not images_metadata:
                logger.warning("no images found in pdf")
                return True
            
            # show extraction stats
            stats = extractor.get_image_stats()
            logger.info(f"\nextraction statistics:")
            logger.info("*"*80)
            logger.info(f"   total images: {stats['total_images']}")
            logger.info(f"   pages with images: {stats['pages_with_images']}")
            logger.info(f"   total size: {stats['total_size'] / 1024:.2f} KB")
            logger.info(f"   formats: {', '.join(stats['formats'])}\n")
            
            # step 2: label with ai
            logger.info("*"*80)
            logger.info("step 2: ai labeling with gpt-4 vision")
            logger.info("*"*80)
            
            labeler = ImageLabeler(config.openai_api_key)
            labeled_metadata = labeler.label_images_batch(images_metadata)
            
            # save labeled metadata
            labeler.save_labeled_metadata(labeled_metadata, metadata_path)
        
        # display results
        logger.info("\n" + "*"*80)
        logger.info("labeled images")
        logger.info("*"*80)
        
        for i, img in enumerate(labeled_metadata, 1):
            logger.info(f"\n[{i}] {img['filename']}")
            logger.info(f"    page number: {img['page_number']}")
            logger.info(f"    size: {img['width']}x{img['height']} pixels")
            logger.info(f"    label: {img.get('label', 'N/A')}")
            logger.info(f"    type: {img.get('image_type', 'N/A')}")
            logger.info(f"    description: {img.get('description', 'N/A')}")
            logger.info(f"    relevance: {img.get('ai_relevance', 'N/A')}")
            if img.get('key_elements'):
                logger.info(f"    key elements: {', '.join(img['key_elements'][:5])}")
        
        logger.info("\n" + "*"*80)
        logger.info("stage 2 complete")
        logger.info("*"*80)
        logger.info(f"images saved to: {images_dir}/")
        logger.info(f"metadata saved to: {metadata_path}")
        logger.info(f"\nnext step: python test_stage3_content.py {pdf_path}")
        logger.info("*"*80 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\nerror during image extraction: {str(e)}")
        logger.error(f"error: {str(e)}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description='extract images from pdf and use ai to label and describe them')
    parser.add_argument('pdf_file', type=str, help='path to the pdf file')
    parser.add_argument('--use-cached', action='store_true', help='use previously extracted images')
    args = parser.parse_args()
  
    try:
        start_time = time.time()
        success = stage2_images(args.pdf_file, args.use_cached)
        end_time = time.time()
        logger.info(f"time taken: {end_time - start_time:.2f} seconds")
    except Exception as e:
        logger.error(f"error during image extraction: {str(e)}")
        logger.error(f"error during image extraction: {str(e)}", exc_info=True)
        sys.exit(1)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

