"""
Context processor utility
Processes large context and splits it into smaller chunks with summaries.
"""

from typing import List, Dict, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI
from utils.logger import get_logger

logger = get_logger(__name__)


class ContextProcessor:
    """
    Processes large context and splits it into smaller chunks.
    
    Args:
        context: The large context to process
        api_key: OpenAI API key
        document_title: The title of the document
        chunk_length: The length of each chunk
        split_by: The character to split the context by
    
    Returns:
        A list of smaller chunks with summaries
    """
    
    def __init__(self, context: str, api_key: str, document_title: str = "Untitled Document", 
                 chunk_length: int = 5000, split_by: str = '\n', prompts_dir: Optional[Path] = None):
        """
        Initialize large context processor.
        
        Args:
            context: The large context to process
            api_key: OpenAI API key
            document_title: The title of the document
            chunk_length: The length of each chunk
            split_by: The character to split the context by
            prompts_dir: Path to prompts directory (from config)
        """
        self.context = context
        self.document_title = document_title
        self.chunk_length = chunk_length
        self.split_by = split_by
        self.client = OpenAI(api_key=api_key)
        
        # Initialize jinja2 environment for prompt templates
        if prompts_dir is None:
            from utils.config_loader import get_config
            config = get_config()
            prompts_dir = config.get_prompts_directory()
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _generate_summary(self, prompt: str) -> str:
        """
        Generate a summary of the context.
        
        Args:
            prompt: The text chunk to summarize
        
        Returns:
            A summary of the context
        """
        # Load system prompt from template
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
        Split the context into smaller chunks.
        
        Returns:
            A list of smaller chunks
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
    
    def get_chunks(self) -> List[Dict]:
        """
        Get the chunks of the context with summaries.
        
        Returns:
            A list of dictionaries with 'chunk' and 'summary' keys
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

