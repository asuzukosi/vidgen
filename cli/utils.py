"""
cli utilities - helper functions for the cli application
"""

import os
import json
from pathlib import Path

from core.logger import get_logger
from core.pdf_parser import PDFParser
from core.image_extractor import ImageExtractor
from core.image_labeler import ImageLabeler
from core.content_analyzer import ContentAnalyzer
from core.stock_image_fetcher import StockImageFetcher
from core.script_generator import ScriptGenerator
from core.voiceover_generator import VoiceoverGenerator
from styles.slideshow import generate_slideshow_video
from styles.animated import generate_animated_video
from styles.ai_generated import generate_ai_video
from styles.combined import generate_combined_video

logger = get_logger(__name__)


def test_phase1(pdf_path: str) -> bool:
    """
    Test Phase 1: PDF Text Extraction
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=== Phase 1: PDF Text Extraction Test ===")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    try:
        with PDFParser(pdf_path) as parser:
            content = parser.extract_structured_content()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"PDF Title: {content['title']}")
            logger.info(f"Total Pages: {content['total_pages']}")
            logger.info(f"Sections Found: {len(content['sections'])}")
            logger.info(f"{'='*60}\n")
            
            for i, section in enumerate(content['sections'], 1):
                logger.info(f"\nSection {i}: {section['title']}")
                logger.info(f"Level: {section['level']}")
                logger.info(f"Content Length: {len(section['content'])} characters")
                
                preview = section['content'][:150].replace('\n', ' ')
                if len(section['content']) > 150:
                    preview += "..."
                logger.info(f"Preview: {preview}\n")
            
            logger.info("✓ Phase 1 Test Completed Successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Error during Phase 1 test: {str(e)}", exc_info=True)
        return False


def test_phase2(pdf_path: str, config) -> bool:
    """
    Test Phase 2: Image Extraction & AI Labeling
    
    Args:
        pdf_path: Path to PDF file
        config: Configuration object
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=== Phase 2: Image Extraction & AI Labeling Test ===")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    if not config.openai_api_key:
        logger.error("OpenAI API key not found. Phase 2 requires OPENAI_API_KEY.")
        return False
    
    try:
        logger.info("\n--- Step 1: Extracting Images ---")
        extractor = ImageExtractor(pdf_path, config.get('output.temp_directory', 'temp') + '/images')
        images_metadata = extractor.extract_images()
        
        if not images_metadata:
            logger.warning("No images found in PDF")
            return True
        
        stats = extractor.get_image_stats()
        logger.info(f"\n{'='*60}")
        logger.info(f"Extracted {stats['total_images']} images")
        logger.info(f"Pages with images: {stats['pages_with_images']}")
        logger.info(f"{'='*60}\n")
        
        logger.info("\n--- Step 2: Labeling Images with AI ---")
        labeler = ImageLabeler(config.openai_api_key)
        labeled_metadata = labeler.label_images_batch(images_metadata)
        
        for i, img in enumerate(labeled_metadata, 1):
            logger.info(f"\n{i}. {img['filename']}")
            logger.info(f"   Label: {img.get('label', 'N/A')}")
            logger.info(f"   Description: {img.get('description', 'N/A')}")
        
        metadata_path = os.path.join(
            config.get('output.temp_directory', 'temp'),
            'images',
            'images_metadata_labeled.json'
        )
        labeler.save_labeled_metadata(labeled_metadata, metadata_path)
        
        logger.info(f"\n✓ Phase 2 Test Completed Successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during Phase 2 test: {str(e)}", exc_info=True)
        return False


def test_phase3(pdf_path: str, config) -> bool:
    """
    Test Phase 3: Content Analysis & Segmentation
    
    Args:
        pdf_path: Path to PDF file
        config: Configuration object
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=== Phase 3: Content Analysis & Segmentation Test ===")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    if not config.openai_api_key:
        logger.error("OpenAI API key not found. Phase 3 requires OPENAI_API_KEY.")
        return False
    
    try:
        logger.info("\n--- Step 1: Parsing PDF ---")
        with PDFParser(pdf_path) as parser:
            pdf_content = parser.extract_structured_content()
        logger.info(f"Parsed {pdf_content['total_pages']} pages")
        
        logger.info("\n--- Step 2: Processing Images ---")
        images_metadata = None
        temp_dir = config.get('output.temp_directory', 'temp')
        images_dir = os.path.join(temp_dir, 'images')
        metadata_path = os.path.join(images_dir, 'images_metadata_labeled.json')
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                images_metadata = json.load(f)
            logger.info(f"Loaded {len(images_metadata)} labeled images")
        else:
            extractor = ImageExtractor(pdf_path, images_dir)
            images_metadata = extractor.extract_images()
            
            if images_metadata:
                labeler = ImageLabeler(config.openai_api_key)
                images_metadata = labeler.label_images_batch(images_metadata)
                labeler.save_labeled_metadata(images_metadata, metadata_path)
        
        logger.info("\n--- Step 3: Creating Video Outline ---")
        analyzer = ContentAnalyzer(
            config.openai_api_key,
            target_segments=config.get('content.target_segments', 7),
            segment_duration=config.get('content.segment_duration', 45)
        )
        outline = analyzer.analyze_content(pdf_content, images_metadata)
        
        if config.get('images.use_stock_images', True):
            fetcher = StockImageFetcher()
            availability = fetcher.is_available()
            
            if availability['unsplash'] or availability['pexels']:
                outline['segments'] = fetcher.fetch_for_segments(
                    outline['segments'],
                    config.get('images.preferred_stock_provider', 'unsplash')
                )
        
        logger.info(f"\nCreated outline with {outline['total_segments']} segments")
        
        outline_path = os.path.join(temp_dir, 'video_outline.json')
        analyzer.save_outline(outline, outline_path)
        
        logger.info("✓ Phase 3 Test Completed Successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during Phase 3 test: {str(e)}", exc_info=True)
        return False


def test_phase4(pdf_path: str, config) -> bool:
    """
    Test Phase 4: Script Generation & Voiceover
    
    Args:
        pdf_path: Path to PDF file
        config: Configuration object
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=== Phase 4: Script Generation & Voiceover Test ===")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    if not config.openai_api_key:
        logger.error("OpenAI API key not found. Phase 4 requires OPENAI_API_KEY.")
        return False
    
    try:
        temp_dir = config.get('output.temp_directory', 'temp')
        outline_path = os.path.join(temp_dir, 'video_outline.json')
        
        if os.path.exists(outline_path):
            logger.info("Loading existing video outline...")
            with open(outline_path, 'r') as f:
                outline = json.load(f)
        else:
            logger.info("Running through Phases 1-3...")
            
            with PDFParser(pdf_path) as parser:
                pdf_content = parser.extract_structured_content()
            
            images_dir = os.path.join(temp_dir, 'images')
            metadata_path = os.path.join(images_dir, 'images_metadata_labeled.json')
            images_metadata = None
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    images_metadata = json.load(f)
            else:
                extractor = ImageExtractor(pdf_path, images_dir)
                images_metadata = extractor.extract_images()
                if images_metadata:
                    labeler = ImageLabeler(config.openai_api_key)
                    images_metadata = labeler.label_images_batch(images_metadata)
                    labeler.save_labeled_metadata(images_metadata, metadata_path)
            
            analyzer = ContentAnalyzer(
                config.openai_api_key,
                target_segments=config.get('content.target_segments', 7),
                segment_duration=config.get('content.segment_duration', 45)
            )
            outline = analyzer.analyze_content(pdf_content, images_metadata)
            analyzer.save_outline(outline, outline_path)
        
        logger.info(f"Loaded outline with {len(outline['segments'])} segments")
        
        logger.info("\n--- Step 1: Generating Scripts ---")
        script_gen = ScriptGenerator(config.openai_api_key)
        script_data = script_gen.generate_script(outline)
        
        script_path = os.path.join(temp_dir, 'video_script.json')
        script_gen.save_script(script_data, script_path)
        
        logger.info(f"Generated {script_data['total_segments']} scripts")
        
        logger.info("\n--- Step 2: Generating Voiceovers ---")
        voiceover_gen = VoiceoverGenerator(
            provider=config.get('voiceover.provider', 'elevenlabs'),
            api_key=config.elevenlabs_api_key,
            voice_id=config.get('voiceover.voice_id'),
            output_dir=os.path.join(temp_dir, 'audio')
        )
        
        result = voiceover_gen.generate_voiceovers(script_data)
        
        audio_metadata_path = os.path.join(temp_dir, 'script_with_audio.json')
        voiceover_gen.save_metadata(result, audio_metadata_path)
        
        logger.info(f"Generated voiceovers for {len(result['segments'])} segments")
        logger.info("✓ Phase 4 Test Completed Successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during Phase 4 test: {str(e)}", exc_info=True)
        return False


def generate_full_video(
    pdf_path: str,
    style: str,
    output_path: str,
    config
) -> bool:
    """
    Run complete pipeline to generate video from PDF.
    
    Args:
        pdf_path: Path to PDF file
        style: Video style ('slideshow', 'animated', 'ai_generated', 'combined')
        output_path: Output video path
        config: Configuration object
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"=== Full Pipeline: PDF to {style.upper()} Video ===")
    logger.info(f"Input: {pdf_path}")
    logger.info(f"Output: {output_path}\n")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    if not config.openai_api_key:
        logger.error("OpenAI API key required for video generation")
        return False
    
    try:
        temp_dir = config.get('output.temp_directory', 'temp')
        script_audio_path = os.path.join(temp_dir, 'script_with_audio.json')
        
        if os.path.exists(script_audio_path):
            logger.info("Found existing script and audio data. Reusing...")
            with open(script_audio_path, 'r') as f:
                script_with_audio = json.load(f)
        else:
            logger.info("Running full content pipeline (Phases 1-4)...\n")
            
            # Phase 1
            logger.info("--- Phase 1: PDF Parsing ---")
            with PDFParser(pdf_path) as parser:
                pdf_content = parser.extract_structured_content()
            logger.info(f"✓ Parsed {pdf_content['total_pages']} pages\n")
            
            # Phase 2
            logger.info("--- Phase 2: Image Extraction & Labeling ---")
            images_dir = os.path.join(temp_dir, 'images')
            extractor = ImageExtractor(pdf_path, images_dir)
            images_metadata = extractor.extract_images()
            
            if images_metadata:
                labeler = ImageLabeler(config.openai_api_key)
                images_metadata = labeler.label_images_batch(images_metadata)
                
                metadata_path = os.path.join(images_dir, 'images_metadata_labeled.json')
                labeler.save_labeled_metadata(images_metadata, metadata_path)
                logger.info(f"✓ Extracted and labeled {len(images_metadata)} images\n")
            else:
                images_metadata = []
            
            # Phase 3
            logger.info("--- Phase 3: Content Analysis & Segmentation ---")
            analyzer = ContentAnalyzer(
                config.openai_api_key,
                target_segments=config.get('content.target_segments', 7),
                segment_duration=config.get('content.segment_duration', 45)
            )
            outline = analyzer.analyze_content(pdf_content, images_metadata)
            
            if config.get('images.use_stock_images', True):
                fetcher = StockImageFetcher()
                if fetcher.is_available()['unsplash'] or fetcher.is_available()['pexels']:
                    outline['segments'] = fetcher.fetch_for_segments(
                        outline['segments'],
                        config.get('images.preferred_stock_provider', 'unsplash')
                    )
            
            outline_path = os.path.join(temp_dir, 'video_outline.json')
            analyzer.save_outline(outline, outline_path)
            logger.info(f"✓ Created outline with {len(outline['segments'])} segments\n")
            
            # Phase 4
            logger.info("--- Phase 4: Script Generation & Voiceover ---")
            script_gen = ScriptGenerator(config.openai_api_key)
            script_data = script_gen.generate_script(outline)
            
            script_path = os.path.join(temp_dir, 'video_script.json')
            script_gen.save_script(script_data, script_path)
            logger.info(f"✓ Generated scripts\n")
            
            voiceover_gen = VoiceoverGenerator(
                provider=config.get('voiceover.provider', 'elevenlabs'),
                api_key=config.elevenlabs_api_key,
                voice_id=config.get('voiceover.voice_id'),
                output_dir=os.path.join(temp_dir, 'audio')
            )
            
            script_with_audio = voiceover_gen.generate_voiceovers(script_data)
            voiceover_gen.save_metadata(script_with_audio, script_audio_path)
            
            combined_audio_path = os.path.join(temp_dir, 'full_voiceover.mp3')
            voiceover_gen.generate_full_audio(script_with_audio, combined_audio_path)
            logger.info(f"✓ Generated voiceovers\n")
        
        # Video generation
        logger.info(f"--- Generating {style.upper()} Video ---\n")
        
        output_dir = os.path.dirname(output_path)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if style == 'slideshow':
            video_path = generate_slideshow_video(script_with_audio, config.config, output_path)
        elif style == 'animated':
            video_path = generate_animated_video(script_with_audio, config.config, output_path)
        elif style == 'ai_generated':
            video_path = generate_ai_video(script_with_audio, config.config, output_path)
        elif style == 'combined':
            video_path = generate_combined_video(script_with_audio, config.config, output_path)
        else:
            logger.error(f"Unknown style: {style}")
            return False
        
        logger.info(f"\n{'='*80}")
        logger.info("✓✓✓ VIDEO GENERATION COMPLETE! ✓✓✓")
        logger.info(f"{'='*80}")
        logger.info(f"Output: {video_path}")
        logger.info(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}", exc_info=True)
        return False

