"""
Text extractor module for extracting field values from text.
Handles pattern matching and value extraction.
"""

from typing import List, Dict, Optional
import re


class TextExtractor:
    """
    Extracts field values from text based on predefined keys.
    """
    
    def __init__(self, extraction_keys: List[str] = None):
        """
        Initialize the text extractor.
        
        Args:
            extraction_keys: List of field names to extract
        """
        self.extraction_keys = extraction_keys or []
    
    def extract_value(self, text: str, key: str) -> str:
        """
        Extract value after a key from the text.
        Handles cases where value is on the same line after key+delimiter,
        or on subsequent lines.
        
        Args:
            text: Full text to search in
            key: Key to search for
            
        Returns:
            Extracted value or empty string if not found
        """
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if key exists in the line
            if key in line_stripped:
                # Get the part after the key
                remaining = line_stripped[len(key):].strip()
                
                # If there's a delimiter (like :), remove it and get the value
                if remaining:
                    # Remove leading delimiters like :, -, etc.
                    remaining = remaining.lstrip(':- ')
                    if remaining:
                        return remaining
                
                # If value is on the next line, check next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line:
                        return next_line
        
        return ""
    
    def extract_all(self, text: str, keys: List[str] = None) -> Dict[str, str]:
        """
        Extract all fields from text.
        
        Args:
            text: Full text to search in
            keys: List of keys to extract (uses instance keys if None)
            
        Returns:
            Dictionary mapping field names to extracted values
        """
        keys_to_use = keys or self.extraction_keys
        extracted_data = {}
        
        for key in keys_to_use:
            value = self.extract_value(text, key)
            extracted_data[key] = value
        
        return extracted_data
    
    def set_keys(self, keys: List[str]):
        """Set extraction keys."""
        self.extraction_keys = keys
    
    def add_key(self, key: str):
        """Add a new extraction key."""
        if key not in self.extraction_keys:
            self.extraction_keys.append(key)
    
    def remove_key(self, key: str):
        """Remove an extraction key."""
        if key in self.extraction_keys:
            self.extraction_keys.remove(key)
    
    def extract_with_regex(self, text: str, pattern: str, group: int = 0) -> str:
        """
        Extract value using regex pattern.
        
        Args:
            text: Text to search in
            pattern: Regex pattern
            group: Group number to return (0 = full match)
            
        Returns:
            Matched value or empty string
        """
        try:
            match = re.search(pattern, text)
            if match:
                return match.group(group)
        except Exception:
            pass
        return ""
    
    def extract_multiple_with_regex(self, text: str, pattern: str) -> List[str]:
        """
        Extract multiple values using regex.
        
        Args:
            text: Text to search in
            pattern: Regex pattern
            
        Returns:
            List of all matches
        """
        try:
            return re.findall(pattern, text)
        except Exception:
            return []
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Trim leading/trailing whitespace
        return text.strip()

