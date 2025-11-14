#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 3: CONTENT ANALYSIS & SEGMENTATION TEST

PURPOSE:
    Analyze document content and create a structured video outline:
    - Break content into 5-10 video segments
    - Match images to relevant segments
    - Fetch stock images for visual variety
    - Generate visual keywords for each segment

APPROACH:
    1. GPT-4 analyzes full document to identify:
       - Main themes and topics
       - Natural narrative flow
       - Key points for each section
    2. Creates time-based segments (30-60s each)
    3. Semantic matching:
       - Matches PDF images to segments by content similarity
       - Generates search keywords for stock images
    4. Stock image APIs (Unsplash/Pexels):
       - Fetches high-quality images based on keywords
       - Provides visual variety for segments without PDF images

OUTPUT:
    - Video outline: temp/video_outline.json
    - Stock images: temp/stock_images/
    - Console output with segment structure

OPTIONS:
    --use-cached     Use previously parsed content and images
    --skip-stock     Skip stock image fetching

USAGE:
    python test_stage3_content.py <pdf_file> [options]
    
EXAMPLES:
    python test_stage3_content.py document.pdf
    python test_stage3_content.py document.pdf --use-cached
    python test_stage3_content.py document.pdf --skip-stock
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logging, get_logger
from core.config_loader import get_config
from core.pdf_parser import PDFParser
from core.image_extractor import ImageExtractor
from core.image_labeler import ImageLabeler
from core.content_analyzer import ContentAnalyzer
from core.stock_image_fetcher import StockImageFetcher

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def test_content_analysis(pdf_path: str, use_cached: bool = False, skip_stock: bool = False):
    """
    Test content analysis and video segmentation.
    
    Args:
        pdf_path: Path to PDF file
        use_cached: Use cached parsing and image results
        skip_stock: Skip stock image fetching
    """
    print("\n" + "="*80)
    print("STAGE 3: CONTENT ANALYSIS & SEGMENTATION")
    print("="*80 + "\n")
    
    config = get_config()
    
    if not config.openai_api_key:
        print("❌ Error: OpenAI API key required")
        return False
    
    if not os.path.exists(pdf_path):
        print("❌ Error: PDF file not found: {pdf_path}")
        return False
    
    try:
        temp_dir = 'temp'
        
        # Step 1: Get PDF content
        print("="*80)
        print("STEP 1: LOADING PDF CONTENT")
        print("="*80 + "\n")
        
        parsed_path = os.path.join(temp_dir, 'parsed_content.json')
        if use_cached and os.path.exists(parsed_path):
            print("📦 Using cached parsed content...")
            with open(parsed_path, 'r') as f:
                pdf_content = json.load(f)
        else:
            print("📄 Parsing PDF...")
            with PDFParser(pdf_path) as parser:
                pdf_content = parser.extract_structured_content()
        
        print(f"✓ Loaded {pdf_content['total_pages']} pages, {len(pdf_content['sections'])} sections\n")
        
        # Step 2: Get images
        print("="*80)
        print("STEP 2: LOADING IMAGES")
        print("="*80 + "\n")
        
        images_metadata = None
        metadata_path = os.path.join(temp_dir, 'images', 'images_metadata_labeled.json')
        
        if os.path.exists(metadata_path):
            print("📦 Loading labeled images...")
            with open(metadata_path, 'r') as f:
                images_metadata = json.load(f)
            print(f"✓ Loaded {len(images_metadata)} labeled images\n")
        else:
            print("⚠️  No labeled images found. Run test_stage2_images.py first.\n")
            images_metadata = []
        
        # Step 3: Create video outline
        print("="*80)
        print("STEP 3: CREATING VIDEO OUTLINE WITH AI")
        print("="*80 + "\n")
        
        analyzer = ContentAnalyzer(
            config.openai_api_key,
            target_segments=config.get('content.target_segments', 7),
            segment_duration=config.get('content.segment_duration', 45)
        )
        
        outline = analyzer.analyze_content(pdf_content, images_metadata)
        
        # Step 4: Fetch stock images
        if not skip_stock and config.get('images.use_stock_images', True):
            print("\n" + "="*80)
            print("STEP 4: FETCHING STOCK IMAGES")
            print("="*80 + "\n")
            
            fetcher = StockImageFetcher()
            availability = fetcher.is_available()
            
            if availability['unsplash'] or availability['pexels']:
                print(f"📸 Stock providers: Unsplash={'✓' if availability['unsplash'] else '✗'}, Pexels={'✓' if availability['pexels'] else '✗'}")
                preferred = config.get('images.preferred_stock_provider', 'unsplash')
                outline['segments'] = fetcher.fetch_for_segments(outline['segments'], preferred)
            else:
                print("⚠️  No stock image API keys configured")
        else:
            print("\n⏭️  Skipping stock images")
        
        # Display results
        print("\n" + "="*80)
        print(f"VIDEO OUTLINE: {outline['title']}")
        print("="*80)
        print(f"Total Segments: {outline['total_segments']}")
        print(f"Estimated Duration: {outline['estimated_duration']}s (~{outline['estimated_duration']//60} min)")
        print("="*80)
        
        for i, segment in enumerate(outline['segments'], 1):
            print(f"\n[{i}] {segment['title']}")
            print(f"    Duration: {segment['duration']}s")
            print(f"    Purpose: {segment.get('purpose', 'N/A')}")
            
            if segment.get('key_points'):
                print(f"    Key Points:")
                for point in segment['key_points'][:3]:
                    print(f"      • {point}")
            
            if segment.get('visual_keywords'):
                print(f"    Visual Keywords: {', '.join(segment['visual_keywords'][:5])}")
            
            # Images
            pdf_images = segment.get('pdf_images', [])
            stock_image = segment.get('stock_image')
            print(f"    Images: {len(pdf_images)} PDF, {'1 Stock' if stock_image else '0 Stock'}")
        
        # Save outline
        outline_path = os.path.join(temp_dir, 'video_outline.json')
        with open(outline_path, 'w', encoding='utf-8') as f:
            json.dump(outline, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*80)
        print("✅ STAGE 3 COMPLETE")
        print("="*80)
        print(f"Outline saved to: {outline_path}")
        print(f"\nNext step: python test_stage4_script.py {pdf_path}")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during content analysis: {str(e)}")
        logger.error(f"Error: {str(e)}", exc_info=True)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_stage3_content.py <pdf_file> [options]")
        print("\nOptions:")
        print("  --use-cached    Use previously parsed content and images")
        print("  --skip-stock    Skip stock image fetching")
        print("\nExamples:")
        print("  python test_stage3_content.py document.pdf")
        print("  python test_stage3_content.py document.pdf --use-cached")
        print("  python test_stage3_content.py document.pdf --skip-stock")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    use_cached = '--use-cached' in sys.argv
    skip_stock = '--skip-stock' in sys.argv
    
    success = test_content_analysis(pdf_path, use_cached, skip_stock)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

