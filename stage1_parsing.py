"""
pdf parsing and text extraction
extract and analyze the structure of a PDF document including:
    - document title and metadata
    - section hierarchy (headings, subheadings)
    - text content organization
    - page information
    approach:
use pdfplumber library to:
    1. extract raw text from each page
    2. identify heading levels based on font size and formatting
    3. group content into logical sections
    4. preserve document structure for later stages
output:
    - structured JSON with sections and content
    - console output showing document hierarchy
    - Saved to: temp/parsed_content.json (or a custom file via --output)
    usage:
    python stage1_parsing.py <pdf_file> [--output output_file.json]
example:
    python stage1_parsing.py document.pdf --output mycontent.json
"""

import sys
import os
import json
from pathlib import Path
import uuid
import argparse
import time

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logging, get_logger
from core.pdf_parser import PDFParser

setup_logging(log_dir='temp')
logger = get_logger(__name__)

def test_pdf_parsing(pdf_path: str, output_path: str = "temp/parsed_content.json"):
    """
    test pdf parsing and structure extraction.
    args:
        pdf_path: path to pdf file
        output_path: destination json for results
    returns:
        True if successful, False otherwise
    """
    logger.info("*"*80)
    logger.info("pdf parsing and text extraction")
    logger.info("*"*80)
    
    if not os.path.exists(pdf_path):
        logger.error(f"pdf file not found: {pdf_path}")
        return False
    
    try:
        # parse PDF
        logger.info(f"parsing pdf: {pdf_path}\n")
        with PDFParser(pdf_path) as parser:
            content = parser.extract_structured_content()
        
        # display results
        logger.info("*"*80)
        logger.info("document information")
        logger.info("*"*80)
        logger.info(f"title:        {content['title']}")
        logger.info(f"total pages:  {content['total_pages']}")
        logger.info(f"sections:     {len(content['sections'])}")
        logger.info(f"total chars:  {sum(len(s['content']) for s in content['sections']):,}")
        logger.info("*"*80 + "\n")
        
        # display section hierarchy
        logger.info("*"*80)
        logger.info("section hierarchy")
        logger.info("*"*80)
        
        for i, section in enumerate(content['sections'], 1):
            indent = "  " * (section['level'] - 1)
            logger.info(f"\n{indent}[{i}] {section['title']}")
            logger.info(f"{indent}    level: {section['level']}")
            logger.info(f"{indent}    pages: {section.get('page_start', '?')} - {section.get('page_end', '?')}")
            logger.info(f"{indent}    length: {len(section['content']):,} characters")
            
            # Show preview
            preview = section['content'][:200].replace('\n', ' ')
            if len(section['content']) > 200:
                preview += "..."
            logger.info(f"{indent}    preview: {preview}")
        
        # Save to file
        out_path = Path(output_path)
        out_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        logger.info("\n" + "*"*80)
        logger.info("stage 1 complete")
        logger.info("*"*80)
        logger.info(f"saved to: {output_path}")
        logger.info(f"next step: python stage2_images.py {pdf_path}")
        logger.info("*"*80 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"error during parsing: {str(e)}")
        logger.error(f"error during parsing: {str(e)}", exc_info=True)
        return False

def main():
    parser = argparse.ArgumentParser(description='parse a pdf file and extract the structure')
    parser.add_argument('pdf_file', type=str, help='path to the pdf file')
    parser.add_argument('--output', '-o', type=str, default="temp/parsed_content.json",
                        help='output JSON file for parsed structure (default: temp/parsed_content.json)')
    args = parser.parse_args()
    
    try:
        start_time = time.time()
        success = test_pdf_parsing(args.pdf_file, args.output)
        end_time = time.time()
        logger.info(f"time taken: {end_time - start_time:.2f} seconds")
    except Exception as e:
        logger.error(f"error during parsing: {str(e)}")
        logger.error(f"error during parsing: {str(e)}", exc_info=True)
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

