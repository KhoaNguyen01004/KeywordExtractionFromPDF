"""
Routes package for the application.
Contains API and web route handlers.
"""

from .api import api_bp
from .web import web_bp

__all__ = ['api_bp', 'web_bp']

