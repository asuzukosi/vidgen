#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vidgen - command line interface
traditional cli for pdf to video generation
"""

import argparse
import sys
import os
from pathlib import Path

# add the project root to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# import centralized logger first
from core.logger import setup_logging, get_logger

# set up logging for the entire application
setup_logging(log_dir='temp')
logger = get_logger(__name__)

from core.config_loader import get_config
from cli.utils import (
    test_phase1,
    test_phase2,
    test_phase3,
    test_phase4,
    generate_full_video
)


def setup_argparse():
    """set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='generate professional explainer videos from pdf documents'
    )
    
    parser.add_argument(
        'pdf',
        type=str,
        help='path to the pdf file'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='output video file path (default: output/video.mp4)'
    )
    
    parser.add_argument(
        '-s', '--style',
        type=str,
        choices=['slideshow', 'animated', 'ai_generated', 'combined'],
        default='slideshow',
        help='video style: slideshow, animated, ai_generated, or combined (ai-selected mix of all styles)'
    )
    
    parser.add_argument(
        '--test-parser',
        action='store_true',
        help='test pdf parsing only (phase 1)'
    )
    
    parser.add_argument(
        '--test-images',
        action='store_true',
        help='test image extraction and labeling (phase 2)'
    )
    
    parser.add_argument(
        '--test-content',
        action='store_true',
        help='test content analysis and segmentation (phase 3)'
    )
    
    parser.add_argument(
        '--test-script',
        action='store_true',
        help='test script generation and voiceover (phase 4)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='path to configuration file'
    )
    
    return parser


def main():
    """main execution function."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # load configuration
    config = get_config(args.config)
    config.ensure_directories()
    
    logger.info("=== pdf to video generator ===")
    logger.info("input pdf: %s", args.pdf)
    logger.info("style: %s", args.style)
    
    # check api keys
    api_status = config.validate_api_keys()
    if not api_status['openai']:
        logger.warning("openai api key not found. some features will be limited.")
    
    # phase 1 test mode
    if args.test_parser:
        success = test_phase1(args.pdf)
        sys.exit(0 if success else 1)
    
    # phase 2 test mode
    if args.test_images:
        success = test_phase2(args.pdf, config)
        sys.exit(0 if success else 1)
    
    # phase 3 test mode
    if args.test_content:
        success = test_phase3(args.pdf, config)
        sys.exit(0 if success else 1)
    
    # phase 4 test mode
    if args.test_script:
        success = test_phase4(args.pdf, config)
        sys.exit(0 if success else 1)
    
    # full pipeline - generate complete video
    logger.info("\n" + "="*80)
    logger.info("full video generation pipeline")
    logger.info("="*80 + "\n")
    
    # determine output path
    if args.output:
        output_path = args.output
    else:
        output_dir = config.get('output.directory', 'output')
        pdf_name = Path(args.pdf).stem
        output_path = os.path.join(output_dir, "%s_%s.mp4" % (pdf_name, args.style))
    
    # generate video
    success = generate_full_video(args.pdf, args.style, output_path, config)
    
    if success:
        logger.info("\n🎉 success! your explainer video is ready!")
        logger.info("📹 watch it at: %s\n", output_path)
    else:
        logger.error("\n❌ video generation failed. check logs above for details.\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
