"""
Main entry point for the Logistics Data Extraction application.
Run: python run.py
"""

import os
import sys
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app import create_app

if __name__ == '__main__':
    # Create Flask app
    app = create_app()
    
    # Get configuration
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Run the app
    print(f"🚀 Starting Logistics Data Extraction Server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"📂 Frontend: http://localhost:{port}")
    print(f"📡 API: http://localhost:{port}/api/extract-all")
    print(f"\nPress CTRL+C to stop the server...\n")
    
    app.run(host=host, port=port, debug=debug)
