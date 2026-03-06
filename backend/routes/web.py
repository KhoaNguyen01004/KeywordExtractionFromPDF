"""
Web routes for serving static files and pages.
"""

from flask import Blueprint, send_from_directory
import os

# Create web blueprint
web_bp = Blueprint('web', __name__)

# Get frontend path from config
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend')


@web_bp.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory(FRONTEND_PATH, 'index.html')


@web_bp.route('/<path:filename>')
def serve_static(filename):
    """
    Serve static files from frontend directory.
    
    Args:
        filename: Name of the file to serve
    """
    return send_from_directory(FRONTEND_PATH, filename)

