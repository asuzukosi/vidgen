import sys
import os
import json

from core.logger import setup_logging, get_logger
from core.config_loader import get_config
from core.pdf_parser import PDFParser
from core.content_analyzer import ContentAnalyzer
from core.stock_image_fetcher import StockImageFetcher

setup_logging(log_dir='temp')
logger = get_logger(__name__)

def _load_parsed_content(pdf_path: str, temp_dir: str='temp', 
                         use_cached: bool = False):
    """
    load parsed content from cache or parse pdf.
    args:
        pdf_path: path to PDF file
        temp_dir: temporary directory to store results
        use_cached: use cached parsing and image results
    """
    logger.info("loading parsed content")
    # load cached content if available
    parsed_path = os.path.join(temp_dir, 'parsed_content.json')
    if use_cached and os.path.exists(parsed_path):
        logger.info(f"using cached parsed content from {parsed_path}")
        with open(parsed_path, 'r') as f:
            pdf_content = json.load(f)
    else:
        logger.info(f"parsing pdf: {pdf_path}")
        with PDFParser(pdf_path) as parser:
            pdf_content = parser.extract_structured_content()
    
    logger.info(f"loaded {pdf_content['total_pages']} pages, {len(pdf_content['sections'])} sections")
    images_metadata = _load_images(temp_dir, use_cached)
    return pdf_content, images_metadata

def _load_images(temp_dir: str='temp', use_cached: bool = False):
    """
    load labeled images from cache or extract from pdf.
    args:
        temp_dir: temporary directory to store results
        use_cached: use cached labeled images
    """
    logger.info("loading labeled images")
    images_metadata = None
    metadata_path = os.path.join(temp_dir, 'images', 'images_metadata_labeled.json')
    if use_cached and os.path.exists(metadata_path):
        logger.info(f"using cached labeled images from {metadata_path}")
        with open(metadata_path, 'r') as f:
            images_metadata = json.load(f)
        logger.info(f"loaded {len(images_metadata)} labeled images")
    else:
        logger.warning("no labeled images found. run test_stage2_images.py first")
        images_metadata = []
    return images_metadata

def create_video_outline(pdf_path: str, 
                          temp_dir: str='temp',
                          use_cached: bool = False, 
                          skip_stock: bool = False,
                          target_segments: int = 7,
                          segment_duration: int = 45):
    """
    analyze content and create video outline.
    args:
        pdf_path: path to PDF file
        temp_dir: temporary directory to store results
        use_cached: use cached parsing and image results
        skip_stock: skip stock image fetching
        target_segments: target number of video segments
        segment_duration: target duration per segment in seconds
    """
    logger.info("beginning video outline creation")
    # load configuration information
    config = get_config()
    # check if openai api key is set and is valid
    if not config.openai_api_key:
        logger.error("openai api key required. please set OPENAI_API_KEY in .env")
        return False
    # check if pdf file exists
    if not os.path.exists(pdf_path):
        logger.error(f"pdf file not found: {pdf_path}")
        return False
    
    try:
        # load parsed content and images
        pdf_content, images_metadata = _load_parsed_content(pdf_path, temp_dir, use_cached)
    except Exception as e:
        logger.error(f"error loading parsed content and images: {str(e)}")
        return False
    
    # create video outline
    logger.info("creating video outline")
    
    try:
        # create content analyzer class with openai api keys and target segments and segment durations
        analyzer = ContentAnalyzer(
        api_key=config.openai_api_key,
            target_segments=target_segments,
            segment_duration=segment_duration
        )
        outline = analyzer.analyze_content(pdf_content, images_metadata)
    except Exception as e:
        logger.error(f"error creating video outline: {str(e)}", exc_info=True)
        return False
    
    # fetch stock images
    if not skip_stock and config.get('images.use_stock_images', True):
        logger.info("fetching stock images")
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

