"""
Extractor package for PDF data extraction.
Provides modular architecture for different document types.
"""

from .base import BaseExtractor, ExtractorRegistry
from .pdf_processor import PDFProcessor
from .text_extractor import TextExtractor
from .customs_extractor import CustomsExtractor, default_extractor
from .ai_extractor import AIExtractor, LogisticsData
from .ocr_processor import OCRProcessor, get_ocr_processor

__all__ = [
    'BaseExtractor',
    'ExtractorRegistry',
    'PDFProcessor', 
    'TextExtractor',
    'CustomsExtractor',
    'default_extractor',
    'AIExtractor',
    'LogisticsData',
    'OCRProcessor',
    'get_ocr_processor'
]
