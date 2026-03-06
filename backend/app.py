"""
Main Flask application entry point.
Refactored to use modular structure for better maintainability and extensibility.
"""

from flask import Flask
from flask_cors import CORS
import os

# Import configuration
from .config import app_config, FLASK_HOST, FLASK_PORT, FLASK_DEBUG

# Import blueprints
from .routes import api_bp, web_bp


def create_app():
    """
    Application factory function.
    Creates and configures the Flask application.
    
    Returns:
        Configured Flask application instance
    """
    # Determine frontend path
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    
    # Create Flask app
    app = Flask(
        __name__,
        static_folder=frontend_path,
        static_url_path=''
    )
    
    # Configure CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)
    
    # Ensure frontend directory exists
    if not os.path.exists(frontend_path):
        os.makedirs(frontend_path)
    
    return app


# Create app instance
app = create_app()


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'version': '1.0.0'}


if __name__ == '__main__':
    print("Starting PDF Extraction Server...")
    print(f"Document Type: {app_config.get_document_type_name()}")
    print(f"Extraction Fields: {len(app_config.extraction_keys)}")
    print(f"Running on http://{FLASK_HOST}:{FLASK_PORT}")
    
    app.run(
        debug=FLASK_DEBUG,
        host=FLASK_HOST,
        port=FLASK_PORT
    )

