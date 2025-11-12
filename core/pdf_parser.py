"""
pdf parser module
extracts text, structure, and metadata from PDF documents.
uses pdfplumber for text extraction and basic structure detection.
"""

import pdfplumber
from typing import Dict, List
import re
from core.logger import get_logger

logger = get_logger(__name__)


class PDFParser:
    """extract and structure content from PDF documents.
    args:
        pdf_path: path to the PDF file
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = None
        self.pages_data = []
        
    def __enter__(self):
        """context manager entry."""
        self.pdf = pdfplumber.open(self.pdf_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """context manager exit."""
        if self.pdf:
            self.pdf.close()
            
    def extract_text(self) -> str:
        """
        extract all text from the PDF document.
        returns:
            complete text content of the PDF document
        """
        if not self.pdf:
            raise ValueError("pdf document not opened. use context manager or call __enter__()")
            
        full_text = []
        for page_num, page in enumerate(self.pdf.pages, 1):
            text = page.extract_text()
            if text:
                full_text.append(text)
                logger.info(f"extracted text from page {page_num}")
        
        return "\n\n".join(full_text)
    
    def extract_structured_content(self) -> Dict:
        """
        extract text with structure information (headings, paragraphs, lists).
        returns:
            dictionary containing structured content
        """
        if not self.pdf:
            raise ValueError("pdf document not opened. use context manager or call __enter__()")
            
        structured_content = {
            "title": self._extract_title(),
            "sections": [],
            "total_pages": len(self.pdf.pages),
            "metadata": self.pdf.metadata
        }
        
        full_text = self.extract_text()
        sections = self._identify_sections(full_text)
        
        structured_content["sections"] = sections
        
        return structured_content
    
    def _extract_title(self) -> str:
        """
        extract document title from metadata or first page.
        returns:
            document title
        """
        # try metadata first
        if self.pdf.metadata and 'Title' in self.pdf.metadata:
            title = self.pdf.metadata['Title']
            if title and len(title.strip()) > 0:
                return title.strip()
        
        # fallback: try to get title from first page
        if self.pdf.pages:
            first_page_text = self.pdf.pages[0].extract_text()
            if first_page_text:
                lines = first_page_text.split('\n')
                for line in lines[:5]:  # Check first 5 lines
                    line = line.strip()
                    if len(line) > 10 and len(line) < 150:  # Reasonable title length
                        return line
        
        return "untitled document"
    
    def _identify_sections(self, text: str) -> List[Dict]:
        """
        identify sections in the text based on headings.
        returns:
            list of sections with title and content
        """
        sections = []
        
        # split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
        current_section = {
            "title": "introduction",
            "content": "",
            "level": 1
        }
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # detect headings (simple heuristic: short lines, possibly with numbers)
            # more sophisticated detection would use font size from PDF
            if self._is_likely_heading(para):
                # save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # start new section
                current_section = {
                    "title": para,
                    "content": "",
                    "level": self._detect_heading_level(para)
                }
            else:
                # add to current section
                current_section["content"] += para + "\n\n"
        
        # add the last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        # if no sections were detected, create one section with all content
        if not sections:
            sections.append({
                "title": "content",
                "content": text,
                "level": 1
            })
        
        logger.info(f"Identified {len(sections)} sections")
        return sections
    
    def _is_likely_heading(self, text: str) -> bool:
        """
        determine if a line of text is likely a heading.
        returns:
            True if likely a heading
        """
        # heuristics for heading detection
        text = text.strip()
        
        # too long for a heading
        if len(text) > 200:
            return False
        
        # Too short
        if len(text) < 3:
            return False
        
        # Contains heading patterns
        heading_patterns = [
            r'^\d+\.',  # Starts with number and dot (1. Introduction)
            r'^Chapter \d+',  # Chapter X
            r'^Section \d+',  # Section X
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS
            r'^\d+\.\d+',  # Numbered subsection (1.1)
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        # short line with mostly capital letters
        if len(text) < 100:
            capital_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if capital_ratio > 0.5:
                return True
        
        return False
    
    def _detect_heading_level(self, heading: str) -> int:
        """
        detect the level of a heading (1 = main, 2 = sub, etc.).
        returns:
            heading level (1-3)
        """
        # check for numbered headings
        if re.match(r'^\d+\.\d+\.\d+', heading):
            return 3
        elif re.match(r'^\d+\.\d+', heading):
            return 2
        elif re.match(r'^\d+\.', heading):
            return 1
        
        # all caps = level 1
        if heading.isupper():
            return 1
        
        # default
        return 2
    
    def get_page_count(self) -> int:
        """
        get the total number of pages in the PDF document.
        
        returns:
            number of pages
        """
        if not self.pdf:
            raise ValueError("pdf document not opened. use context manager or call __enter__()")
        return len(self.pdf.pages)
    
    def extract_text_by_page(self) -> List[str]:
        """
        extract text from each page separately.
        returns:
            list of text content per page
        """
        if not self.pdf:
            raise ValueError("PDF not opened")
            
        pages_text = []
        for page in self.pdf.pages:
            text = page.extract_text()
            pages_text.append(text if text else "")
        
        return pages_text


def parse_pdf(pdf_path: str) -> Dict:
    """
    convenience function to parse a pdf document and return structured content.
    args:
        pdf_path: path to the pdf document
    returns:
        structured content dictionary
    """
    with PDFParser(pdf_path) as parser:
        return parser.extract_structured_content()


if __name__ == "__main__":
    # test the parser
    import sys
    
    if len(sys.argv) < 2:
        print("usage: python pdf_parser.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print(f"\n**** parsing pdf: {pdf_path} ****")
    
    with PDFParser(pdf_path) as parser:
        # get structured content
        content = parser.extract_structured_content()
        
        logger.info(f"title: {content['title']}")
        logger.info(f"total pages: {content['total_pages']}")
        logger.info(f"sections found: {len(content['sections'])}")
        
        for i, section in enumerate(content['sections'], 1):
            logger.info(f"---- section {i}: {section['title']} (level {section['level']}) ----")
            preview = section['content'][:200] + "..." if len(section['content']) > 200 else section['content']
            logger.info(preview)
        
        logger.info("**** extraction complete ****")

