"""
Test file to verify all modules can be imported correctly.
Run: python test_imports.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all module imports."""
    print("Testing module imports...")
    
    try:
        print("✓ Importing backend.extractor.ai_extractor...")
        from backend.extractor.ai_extractor import AIExtractor, LogisticsData, Container
        print("  - AIExtractor: OK")
        print("  - LogisticsData: OK")
        print("  - Container: OK")
    except Exception as e:
        print(f"✗ Error importing ai_extractor: {e}")
        return False
    
    try:
        print("✓ Importing backend.services.validator...")
        from backend.services.validator import CrossCheckValidator, ValidationFlag, FlagStatus
        print("  - CrossCheckValidator: OK")
        print("  - ValidationFlag: OK")
        print("  - FlagStatus: OK")
    except Exception as e:
        print(f"✗ Error importing validator: {e}")
        return False
    
    try:
        print("✓ Importing backend.routes.api...")
        from backend.routes.api import api_bp
        print("  - api_bp: OK")
    except Exception as e:
        print(f"✗ Error importing api: {e}")
        return False
    
    try:
        print("✓ Importing backend.app...")
        from backend.app import create_app
        print("  - create_app: OK")
    except Exception as e:
        print(f"✗ Error importing app: {e}")
        return False
    
    print("\n✅ All imports successful!")
    return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
