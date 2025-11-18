import sys
import os
import json
import argparse
from typing import List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.logger import setup_logging, get_logger
from core.config_loader import get_config
from core.pdf_parser import PDFParser
from openai import OpenAI
from core.content_analyzer import ContentAnalyzer
from core.stock_image_fetcher import StockImageFetcher

setup_logging(log_dir='temp')
logger = get_logger(__name__)

class LargeContextProcessor:
    """
    processes large context and splits it into smaller chunks.
    args:
        context: the large context to process
        document_title: the title of the document
        chunk_length: the length of each chunk
        split_by: the character to split the context by
    returns:
        a list of smaller chunks
    """
    def __init__(self, context: str, api_key: str, document_title: str = "Untitled Document", chunk_length: int = 5000, split_by: str = '\n'):
        self.context = context
        self.document_title = document_title
        self.chunk_length = chunk_length
        self.split_by = split_by
        self.client = OpenAI(api_key=api_key)
        
        # initialize jinja2 environment for prompt templates
        prompts_dir = Path(__file__).parent / 'prompts'
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _generate_summary(self, prompt: str) -> str:
        """
        generates a summary of the context.
        returns:
            a summary of the context
        """
        # load system prompt from template
        system_template = self.jinja_env.get_template('bullet_summary_system.j2')
        system_prompt = system_template.render(document_title=self.document_title)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content

    def _split_context(self) -> List[str]:
        """
        splits the context into smaller chunks.
        returns:
            a list of smaller chunks
        """
        all_segments = self.context.split(self.split_by)
        chunks = []
        current_chunk = ""
        for segment in all_segments:
            if len(current_chunk) + len(segment) > self.chunk_length:
                chunks.append(current_chunk)
                current_chunk = ""
            current_chunk += segment + self.split_by
        if current_chunk:
            chunks.append(current_chunk)
        return chunks
    
    def get_chunks(self) -> List[str]:
        """
        gets the chunks of the context.
        returns:
            a list of smaller chunks
        """
        chunks = self._split_context()
        data = []
        for chunk in chunks:
            summary = self._generate_summary(chunk)
            data.append({
                'chunk': chunk,
                'summary': summary
            })
        return data
    
def _load_parsed_content(pdf_path: str, temp_dir:str='temp',
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
    
    # load parsed content
    try:
        pdf_content, images_metadata = _load_parsed_content(pdf_path, temp_dir, use_cached)
        logger.info(f"loaded {len(pdf_content['sections'])} sections and {len(images_metadata)} images")
        all_content = ""
        for section in pdf_content['sections']:
            all_content += section['content']
    except Exception as e:
        logger.error(f"error loading parsed content and images: {str(e)}")
        return False
    
    # process large context
    try:
        logger.info("processing large context")
        context_processor = LargeContextProcessor(all_content, config.openai_api_key, pdf_content['title'], chunk_length=4000, split_by='\n')
        chunks = context_processor.get_chunks()
        logger.info(f"generated {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"error processing large context: {str(e)}")
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
        fetcher = StockImageFetcher(config.unsplash_access_key, config.pexels_api_key)
        availability = fetcher.is_available()
        if availability['unsplash'] or availability['pexels']:
            logger.info(f"stock providers: unsplash={availability['unsplash']}, pexels={availability['pexels']}")
            preferred = config.get('images.preferred_stock_provider', 'unsplash')
            outline['segments'] = fetcher.fetch_for_segments(outline['segments'], preferred)
        else:
            logger.info("no stock image API keys configured")
    else:
        logger.info("skipping stock images")

    # save outline
    logger.info("saving video outline")
    outline_path = os.path.join(temp_dir, 'video_outline.json')
    with open(outline_path, 'w', encoding='utf-8') as f:
        json.dump(outline, f, indent=2, ensure_ascii=False)
    logger.info(f"video outline saved to {outline_path}")
    return True

def main():
    # get pdf path from command line
    paerser = argparse.ArgumentParser(description='create video outline from pdf')
    paerser.add_argument('pdf_path', type=str, help='path to the pdf file')
    paerser.add_argument('--use-cached', action='store_true', help='use previously parsed content and images')
    paerser.add_argument('--skip-stock', action='store_true', help='skip stock image fetching')
    paerser.add_argument('--target-segments', type=int, default=7, help='target number of video segments')
    paerser.add_argument('--segment-duration', type=int, default=45, help='target duration per segment in seconds')
    args = paerser.parse_args()
    # get arguments
    pdf_path = args.pdf_path
    use_cached = args.use_cached
    skip_stock = args.skip_stock
    target_segments = args.target_segments
    segment_duration = args.segment_duration
    # create video outline
    create_video_outline(pdf_path, temp_dir='temp', 
                         use_cached=use_cached, 
                         skip_stock=skip_stock,
                         target_segments=target_segments,
                         segment_duration=segment_duration)


if __name__ == "__main__":
    main()

