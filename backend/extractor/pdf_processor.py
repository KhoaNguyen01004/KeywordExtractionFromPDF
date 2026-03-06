"""
PDF processor module using PyMuPDF.
Handles PDF document reading and text extraction.
"""

import fitz
from typing import Optional


class PDFProcessor:
    """
    Handles PDF document processing using PyMuPDF.
    """
    
    def __init__(self):
        """Initialize the PDF processor."""
        pass
    
    def open(self, pdf_content: bytes) -> fitz.Document:
        """
        Open a PDF from bytes.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            PyMuPDF Document object
        """
        return fitz.open(stream=pdf_content, filetype="pdf")
    
    def extract_text(self, pdf_document: fitz.Document) -> str:
        """
        Extract text from all pages of a PDF document.
        
        Args:
            pdf_document: PyMuPDF Document object
            
        Returns:
            Combined text from all pages
        """
        full_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            full_text += page.get_text() + "\n"
        return full_text
    
    def extract_text_from_page(self, pdf_document: fitz.Document, page_num: int) -> str:
        """
        Extract text from a specific page.
        
        Args:
            pdf_document: PyMuPDF Document object
            page_num: Page number (0-indexed)
            
        Returns:
            Text from the specified page
        """
        if 0 <= page_num < len(pdf_document):
            return pdf_document[page_num].get_text()
        return ""
    
    def get_page_count(self, pdf_document: fitz.Document) -> int:
        """
        Get the number of pages in a PDF.
        
        Args:
            pdf_document: PyMuPDF Document object
            
        Returns:
            Number of pages
        """
        return len(pdf_document)
    
    def is_valid_pdf(self, pdf_content: bytes) -> bool:
        """
        Check if the content is a valid PDF.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            doc = self.open(pdf_content)
            is_valid = doc.is_pdf and len(doc) > 0
            doc.close()
            return is_valid
        except Exception:
            return False
    
    def process(self, pdf_content: bytes) -> str:
        """
        Convenience method to process PDF and extract all text.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Combined text from all pages
        """
        doc = None
        try:
            doc = self.open(pdf_content)
            return self.extract_text(doc)
        finally:
            if doc:
                doc.close()
    
    def get_metadata(self, pdf_document: fitz.Document) -> dict:
        """
        Extract metadata from PDF document.
        
        Args:
            pdf_document: PyMuPDF Document object
            
        Returns:
            Dictionary containing metadata
        """
        metadata = pdf_document.metadata
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "page_count": len(pdf_document)
        }

