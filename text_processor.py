# text_processor.py

from typing import List, Dict
import re
import PyPDF2
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self, chunk_size: int = 256, chunk_overlap: int = 25):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def read_pdf(self, file_path: str) -> str:
        """Read text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            raise
    
    def process_text(self, text: str) -> List[Dict]:
        """Process text into structured sections"""
        try:
            sections = []
            current_chapter = ""
            
            # Split text into lines
            lines = text.split('\n')
            
            # Patterns
            section_pattern = r'(\d+)\.\s*(.*?)\s*\.—'
            current_section = None
            current_title = ""
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for chapter
                if line.startswith('CHAPTER'):
                    current_chapter = line
                    continue
                
                # Check for new section
                match = re.match(section_pattern, line)
                if match:
                    # Save previous section
                    if current_section:
                        sections.append({
                            'section_num': current_section,
                            'title': current_title,
                            'content': ' '.join(current_content),
                            'chapter': current_chapter
                        })
                    
                    # Start new section
                    current_section = match.group(1)
                    current_title = match.group(2)
                    current_content = []
                elif current_section:
                    current_content.append(line)
            
            # Add last section
            if current_section:
                sections.append({
                    'section_num': current_section,
                    'title': current_title,
                    'content': ' '.join(current_content),
                    'chapter': current_chapter
                })
            
            return sections
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            chunks.append(chunk)
        
        return chunks