"""
Base extractor class for PDF data extraction.
Defines the interface that all extractors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseExtractor(ABC):
    """
    Abstract base class for document extractors.
    All custom extractors should inherit from this class.
    """
    
    def __init__(self, extraction_keys: List[str] = None):
        """
        Initialize the extractor with extraction keys.
        
        Args:
            extraction_keys: List of field names to extract from documents
        """
        self.extraction_keys = extraction_keys or []
    
    @abstractmethod
    def extract(self, document_content: bytes) -> Dict[str, str]:
        """
        Extract data from document content.
        
        Args:
            document_content: Raw document content (PDF bytes)
            
        Returns:
            Dictionary mapping field names to extracted values
        """
        pass
    
    @abstractmethod
    def validate(self, document_content: bytes) -> bool:
        """
        Validate if the document can be processed.
        
        Args:
            document_content: Raw document content
            
        Returns:
            True if document is valid for this extractor
        """
        pass
    
    def get_supported_fields(self) -> List[str]:
        """Get list of supported extraction fields."""
        return self.extraction_keys
    
    def add_field(self, field_name: str):
        """Add a new field to extract."""
        if field_name not in self.extraction_keys:
            self.extraction_keys.append(field_name)
    
    def remove_field(self, field_name: str):
        """Remove a field from extraction."""
        if field_name in self.extraction_keys:
            self.extraction_keys.remove(field_name)


class ExtractorRegistry:
    """
    Registry for managing multiple extractor types.
    Allows easy switching between different document types.
    """
    
    _extractors: Dict[str, BaseExtractor] = {}
    _default_extractor: str = None
    
    @classmethod
    def register(cls, name: str, extractor: BaseExtractor, is_default: bool = False):
        """
        Register a new extractor.
        
        Args:
            name: Unique identifier for the extractor
            extractor: Instance of BaseExtractor
            is_default: Set as default extractor if True
        """
        cls._extractors[name] = extractor
        if is_default or cls._default_extractor is None:
            cls._default_extractor = name
    
    @classmethod
    def get(cls, name: str = None) -> BaseExtractor:
        """
        Get an extractor by name or return default.
        
        Args:
            name: Extractor name, or None for default
            
        Returns:
            BaseExtractor instance
        """
        if name is None:
            name = cls._default_extractor
        return cls._extractors.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseExtractor]:
        """Get all registered extractors."""
        return cls._extractors.copy()
    
    @classmethod
    def list_extractors(cls) -> List[str]:
        """Get list of available extractor names."""
        return list(cls._extractors.keys())

