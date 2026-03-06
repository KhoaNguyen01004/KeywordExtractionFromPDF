"""
Helper utility functions.
"""

from typing import Set


def validate_file_extension(filename: str, allowed_extensions: Set[str]) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions (e.g., {'pdf'})
        
    Returns:
        True if extension is allowed, False otherwise
    """
    if not filename:
        return False
    
    # Get extension without dot
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in {e.lstrip('.') for e in allowed_extensions}


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    else:
        return f'{size_bytes / (1024 * 1024):.1f} MB'


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing potentially dangerous characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    # Remove non-alphanumeric characters except dots, dashes, underscores
    return re.sub(r'[^\w\-.]', '_', filename)


def create_success_response(data=None, message: str = None):
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Optional success message
        
    Returns:
        Dictionary with success response structure
    """
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return response


def create_error_response(error: str, status_code: int = 400):
    """
    Create a standardized error response.
    
    Args:
        error: Error message
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return {'success': False, 'error': error}, status_code

