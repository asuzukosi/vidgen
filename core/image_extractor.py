"""
pdf image extractor module
extracts images from pdf documents and saves them with metadata.
uses pymupdf (fitz) for robust image extraction.
"""

import fitz  # pymupdf
from PIL import Image
import io
import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict
from core.logger import get_logger

logger = get_logger(__name__)


class ImageExtractor:
    """extract images from pdf documents.
    args:
        pdf_path: path to the pdf document
        output_dir: directory to save extracted images
    """
    
    def __init__(self, pdf_path: str, output_dir: str = "temp/images"):
        """
        initialize image extractor.
        args:
            pdf_path: path to the pdf document
            output_dir: directory to save extracted images
        """
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.images_data = []
        
        # create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
    def extract_images(self, min_width: int = 100, min_height: int = 100) -> List[Dict]:
        """
        extract all images from the pdf document.
        args:
            min_width: minimum image width to extract (filters small icons)
            min_height: minimum image height to extract
        returns:
            list of dictionaries containing image metadata
        """
        logger.info(f"Starting image extraction from {self.pdf_path}")
        # open pdf document
        pdf_document = fitz.open(self.pdf_path)
        # initialize image count
        image_count = 0
        # iterate over pages
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            image_list = page.get_images(full=True)
            # log number of images found on the page
            logger.info(f"Page {page_num + 1}: Found {len(image_list)} images")
            # iterate over images on the page
            for img_index, img_info in enumerate(image_list):
                try:
                    # extract image data
                    xref = img_info[0]
                    base_image = pdf_document.extract_image(xref)
                    # get image bytes and metadata
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    # filter out small images (likely icons or decorations)
                    if width < min_width or height < min_height:
                        logger.debug(f"Skipping small image: {width}x{height}")
                        continue
                    # generate unique filename using hash
                    image_hash = hashlib.md5(image_bytes).hexdigest()[:10]
                    filename = f"img_p{page_num + 1}_{img_index}_{image_hash}.{image_ext}"
                    filepath = os.path.join(self.output_dir, filename)
                    # save image
                    with open(filepath, "wb") as img_file:
                        img_file.write(image_bytes)
                    # get additional metadata
                    try:
                        with Image.open(io.BytesIO(image_bytes)) as pil_img:
                            format_name = pil_img.format
                            mode = pil_img.mode
                    except Exception:
                        format_name = image_ext
                        mode = "unknown"
                    # get surrounding text context (text near the image on the page)
                    text_context = self._extract_text_context(page, img_info)
                    # store metadata
                    image_metadata = {
                        "filename": filename,
                        "filepath": filepath,
                        "page_number": page_num + 1,
                        "width": width,
                        "height": height,
                        "format": format_name,
                        "mode": mode,
                        "size_bytes": len(image_bytes),
                        "text_context": text_context,
                        "xref": xref,
                        "index_on_page": img_index,
                        "label": None,  # To be filled by image_labeler
                        "description": None,  # To be filled by image_labeler
                        "relevance_score": None  # To be filled by content_analyzer
                    }
                    # add metadata to list
                    self.images_data.append(image_metadata)
                    image_count += 1
                    # log image extraction
                    logger.info(f"Extracted image {image_count}: {filename} ({width}x{height})")
                    
                except Exception as e:
                    logger.error(f"Error extracting image {img_index} from page {page_num + 1}: {str(e)}")
                    continue
        logger.info(f"Extracted {image_count} images from {len(pdf_document)} pages")
        pdf_document.close()
        # log image extraction
        # save metadata to json
        self._save_metadata()
        # return images data
        return self.images_data
    
    def _extract_text_context(self, page, img_info, context_chars: int = 500) -> str:
        """
        extract text near an image on the page.
        args:
            page: pdf page object
            img_info: image information
            context_chars: number of characters to extract
        returns:
            text context surrounding the image
        """
        try:
            # get all text from the page
            page_text = page.get_text()
            # return a snippet of the page text
            if len(page_text) > context_chars:
                return page_text[:context_chars]
            return page_text
            
        except Exception as e:
            logger.debug(f"could not extract text context: {str(e)}")
            return ""
    
    def _save_metadata(self):
        """save image metadata to json file."""
        metadata_path = os.path.join(self.output_dir, "images_metadata.json")
        # save metadata to json file
        with open(metadata_path, 'w') as f:
            json.dump(self.images_data, f, indent=2)
        
        logger.info(f"saved metadata to {metadata_path}")
    
    def load_metadata(self) -> List[Dict]:
        """
        load previously saved image metadata.
        returns:
            list of image metadata dictionaries
        """
        metadata_path = os.path.join(self.output_dir, "images_metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.images_data = json.load(f)
            logger.info(f"Loaded metadata for {len(self.images_data)} images")
            return self.images_data
        else:
            logger.warning("No metadata file found")
            return []
    
    def get_images_by_page(self, page_number: int) -> List[Dict]:
        """
        get all images from a specific page.
        args:
            page_number: page number (1-indexed)
        returns:
            list of image metadata for that page
        """
        return [img for img in self.images_data if img['page_number'] == page_number]
    
    def get_image_stats(self) -> Dict:
        """
        get statistics about extracted images.
        returns:
            dictionary with image statistics
        """
        if not self.images_data:
            return {
                "total_images": 0,
                "average_size": 0,
                "formats": {},
                "pages_with_images": 0
            }
        # get total size of all images
        total_size = sum(img['size_bytes'] for img in self.images_data)
        # get formats of all images
        formats = {}
        # iterate over images
        for img in self.images_data:
            fmt = img.get('format', 'unknown')
            formats[fmt] = formats.get(fmt, 0) + 1
        
        return {
            "total_images": len(self.images_data),
            "average_size": total_size // len(self.images_data) if self.images_data else 0,
            "total_size": total_size,
            "formats": formats,
            "pages_with_images": len(set(img['page_number'] for img in self.images_data))
        }


def extract_images_from_pdf(pdf_path: str, output_dir: str = "temp/images") -> List[Dict]:
    """
    convenience function to extract images from a pdf document.
    args:
        pdf_path: path to the pdf document
        output_dir: directory to save images
    returns:
        list of image metadata
    """
    extractor = ImageExtractor(pdf_path, output_dir)
    return extractor.extract_images()


if __name__ == "__main__":
    # test vidgen image extractor
    import sys
    # check if pdf path is provided
    if len(sys.argv) < 2:
        print("usage: python image_extractor.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print(f"**** extracting images from pdf: {pdf_path} ****")
    
    extractor = ImageExtractor(pdf_path)
    images = extractor.extract_images()
    
    print(f"**** extraction summary ****")
    stats = extractor.get_image_stats()
    print(f"total images extracted: {stats['total_images']}")
    print(f"pages with images: {stats['pages_with_images']}")
    print(f"average image size: {stats['average_size'] / 1024:.2f} KB")
    print(f"total size: {stats['total_size'] / 1024:.2f} KB")
    print(f"formats: {stats['formats']}")
    
    print(f"**** image details ****")
    for i, img in enumerate(images, 1):
        print(f"{i}. {img['filename']}")
        print(f"- page: {img['page_number']}, size: {img['width']}x{img['height']}")
        print(f"- format: {img['format']}, size: {img['size_bytes'] / 1024:.2f} KB")
        if img['text_context']:
            preview = img['text_context'][:100].replace('\n', ' ')
            print(f"- context: {preview}...")
    
    print("**** extraction complete ****")

