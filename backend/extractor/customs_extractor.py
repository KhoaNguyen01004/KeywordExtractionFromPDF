"""
Customs declaration extractor - concrete implementation.
Extracts fields from Vietnamese customs declaration PDFs.
"""

from typing import Dict, List
from .base import BaseExtractor
from .pdf_processor import PDFProcessor
from .text_extractor import TextExtractor


class CustomsExtractor(BaseExtractor):
    """
    Concrete extractor for Vietnamese customs declaration documents.
    """
    
    def __init__(self, extraction_keys: List[str] = None):
        """
        Initialize the customs extractor.
        
        Args:
            extraction_keys: List of field names to extract
        """
        super().__init__(extraction_keys)
        self.pdf_processor = PDFProcessor()
        self.text_extractor = TextExtractor(extraction_keys)
    
    def extract(self, document_content: bytes) -> Dict[str, str]:
        """
        Extract data from customs declaration PDF.
        
        Args:
            document_content: PDF file content as bytes
            
        Returns:
            Dictionary mapping field names to extracted values
        """
        # Process PDF to get text
        text = self.pdf_processor.process(document_content)
        
        # Update text extractor with current keys
        self.text_extractor.set_keys(self.extraction_keys)
        
        # Extract all fields
        return self.text_extractor.extract_all(text)
    
    def validate(self, document_content: bytes) -> bool:
        """
        Validate if the document is a valid PDF.
        
        Args:
            document_content: PDF file content
            
        Returns:
            True if valid PDF
        """
        return self.pdf_processor.is_valid_pdf(document_content)
    
    def extract_single(self, document_content: bytes, key: str) -> str:
        """
        Extract a single field from the document.
        
        Args:
            document_content: PDF file content
            key: Field name to extract
            
        Returns:
            Extracted value or empty string
        """
        text = self.pdf_processor.process(document_content)
        return self.text_extractor.extract_value(text, key)


# Default extractor instance
default_extractor = CustomsExtractor()

