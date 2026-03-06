"""
Configuration module for the PDF Extraction application.
Contains all configurable settings including extraction keys.
"""

import os

# Flask settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True

# Frontend path (relative to backend directory)
FRONTEND_PATH = '../frontend'

# Default extraction keys for Vietnamese customs documents
DEFAULT_EXTRACTION_KEYS = [
    "Số vận đơn",
    "Mã số hàng hóa đại diện tờ khai",
    "Mã bộ phận xử lý tờ khai",
    "Người xuất khẩu",
    "Người nhập khẩu",
    "Địa điểm lưu kho",
    "Địa điểm dỡ hàng",
    "Ngày hàng đi",
    "Ngày hàng đến"
]

# Document type configurations
# Each document type can have its own extraction keys
DOCUMENT_TYPES = {
    "customs_declaration": {
        "name": "Tờ khai hải quan",
        "keys": DEFAULT_EXTRACTION_KEYS
    }
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

# Maximum file size (in bytes) - 10MB
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


class Config:
    """Application configuration class."""
    
    def __init__(self, document_type='customs_declaration'):
        self.document_type = document_type
        self._extraction_keys = None
    
    @property
    def extraction_keys(self):
        """Get extraction keys based on document type."""
        if self._extraction_keys is None:
            doc_config = DOCUMENT_TYPES.get(self.document_type, DOCUMENT_TYPES['customs_declaration'])
            self._extraction_keys = doc_config.get('keys', DEFAULT_EXTRACTION_KEYS)
        return self._extraction_keys
    
    @extraction_keys.setter
    def extraction_keys(self, keys):
        """Set custom extraction keys."""
        self._extraction_keys = keys
    
    def add_document_type(self, type_name, name, keys):
        """Add a new document type configuration."""
        DOCUMENT_TYPES[type_name] = {
            "name": name,
            "keys": keys
        }
    
    def get_document_type_name(self):
        """Get the display name for current document type."""
        doc_config = DOCUMENT_TYPES.get(self.document_type, DOCUMENT_TYPES['customs_declaration'])
        return doc_config.get('name', 'Unknown')


# Global configuration instance
app_config = Config()

