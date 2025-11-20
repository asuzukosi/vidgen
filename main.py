#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vidgen - command line interface
traditional cli for pdf to video generation
"""

import argparse
import sys

# import centralized logger first
from utils.logger import setup_logging, get_logger

# set up logging for the entire application
setup_logging(log_dir='temp')
logger = get_logger(__name__)

from utils.config_loader import get_config
from cli.utils import (
    parse_document,
    extract_images,
    analyze_content,
    generate_script,
    generate_full_video
)
from core.pipeline_data import PipelineData


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
        '--parse-document',
        action='store_true',
        help='parse document only (stage 1)'
    )
    
    parser.add_argument(
        '--extract-images',
        action='store_true',
        help='extract images and label with AI (stage 2)'
    )
    
    parser.add_argument(
        '--analyze-content',
        action='store_true',
        help='analyze content and create outline (stage 3)'
    )
    
    parser.add_argument(
        '--generate-script',
        action='store_true',
        help='generate scripts and voiceovers (stage 4)'
    )
    
    parser.add_argument(
        '--pipeline-id',
        type=str,
        default=None,
        help='UUID of pipeline data (required for stages 2-5)'
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
    
    logger.info("pdf to video generator started")
    logger.info("input pdf: %s", args.pdf)
    
    # check api keys
    api_status = config.validate_api_keys()
    if not api_status['openai']:
        logger.warning("openai api key not found. some features will be limited.")
    
    # parse document mode (stage 1 - creates new pipeline)
    if args.parse_document:
        pipeline_data = parse_document(args.pdf, None)
        logger.info("pipeline id: %s", pipeline_data.id)
        sys.exit(0 if pipeline_data.status == "completed" else 1)
    
    # extract images mode (stage 2 - requires pipeline_id)
    if args.extract_images:
        if not args.pipeline_id:
            logger.error("--pipeline-id is required for extract-images")
            sys.exit(1)
        temp_dir = config.get('output.temp_directory', 'temp')
        pipeline_data = PipelineData.load_by_id(args.pipeline_id, temp_dir)
        pipeline_data = extract_images(args.pdf, pipeline_data)
        sys.exit(0 if pipeline_data.status == "completed" else 1)
    
    # analyze content mode (stage 3 - requires pipeline_id)
    if args.analyze_content:
        if not args.pipeline_id:
            logger.error("--pipeline-id is required for analyze-content")
            sys.exit(1)
        temp_dir = config.get('output.temp_directory', 'temp')
        pipeline_data = PipelineData.load_by_id(args.pipeline_id, temp_dir)
        pipeline_data = analyze_content(args.pdf, pipeline_data)
        sys.exit(0 if pipeline_data.status == "completed" else 1)
    
    # generate script mode (stage 4 - requires pipeline_id)
    if args.generate_script:
        if not args.pipeline_id:
            logger.error("--pipeline-id is required for generate-script")
            sys.exit(1)
        temp_dir = config.get('output.temp_directory', 'temp')
        pipeline_data = PipelineData.load_by_id(args.pipeline_id, temp_dir)
        pipeline_data = generate_script(pipeline_data)
        sys.exit(0 if pipeline_data.status == "completed" else 1)
    
    # full pipeline - generate complete video
    logger.info("starting full video generation pipeline")
    
    # generate video (output path will be determined using pipeline ID)
    pipeline_data = generate_full_video(args.pdf, args.output, config)
    
    if pipeline_data.status == "completed" and pipeline_data.video_path:
        logger.info("success! explainer video is ready.")
        logger.info("video path: %s", pipeline_data.video_path)
        logger.info("pipeline id: %s", pipeline_data.id)
        
        # Display timing information
        if pipeline_data.stage_timings:
            logger.info("stage timings:")
            for stage, timing in pipeline_data.stage_timings.items():
                if 'duration' in timing:
                    logger.info("  %s: %.2fs", stage, timing['duration'])
            total = sum(t.get('duration', 0) for t in pipeline_data.stage_timings.values() if 'duration' in t)
            logger.info("  total: %.2fs", total)
    else:
        logger.error("video generation failed. check logs above for details.")
        logger.error("pipeline id: %s", pipeline_data.id)
    
    sys.exit(0 if pipeline_data.status == "completed" else 1)


if __name__ == "__main__":
    main()
