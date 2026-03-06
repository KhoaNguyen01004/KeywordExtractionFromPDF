"""
Example script demonstrating how to use AIExtractor and CrossCheckValidator.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.extractor.ai_extractor import AIExtractor
from backend.services.validator import CrossCheckValidator


def example_extract_single_file():
    """Example: Extract data from a single file."""
    print("\n" + "="*60)
    print("Example 1: Extract data from a single file")
    print("="*60)
    
    # Initialize extractor
    extractor = AIExtractor()
    
    # File path (replace with your actual file)
    file_path = "sample_invoice.pdf"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print("   Please provide a valid PDF file path")
        return None
    
    try:
        print(f"\nExtracting data from: {file_path}")
        data = extractor.extract_data(file_path)
        
        print("\n📄 Extracted Data:")
        print(f"  Document Type: {data.doc_type}")
        print(f"  BL Number: {data.bl_no}")
        print(f"  Invoice Number: {data.invoice_no}")
        print(f"  Shipper: {data.shipper}")
        print(f"  Consignee: {data.consignee}")
        print(f"  Vessel: {data.vessel}")
        print(f"  Total Weight: {data.total_weight} KG")
        print(f"  Total Packages: {data.total_packages}")
        print(f"  Containers: {len(data.containers)}")
        for container in data.containers:
            print(f"    - {container.container_no} (Seal: {container.seal_no})")
        print(f"  HS Code Suggestions: {', '.join(data.hs_code_suggestions)}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return None


def example_cross_check():
    """Example: Cross-check multiple documents."""
    print("\n" + "="*60)
    print("Example 2: Cross-check multiple documents")
    print("="*60)
    
    # Initialize extractor and validator
    extractor = AIExtractor()
    validator = CrossCheckValidator()
    
    # Files to process (replace with your actual files)
    files = [
        "sample_invoice.pdf",
        "sample_packing_list.pdf",
        "sample_bill_of_lading.pdf"
    ]
    
    # Check if files exist
    missing_files = [f for f in files if not os.path.exists(f)]
    if missing_files:
        print(f"\n❌ Files not found: {', '.join(missing_files)}")
        print("   Please provide valid PDF files")
        return
    
    print(f"\nProcessing {len(files)} documents...")
    
    try:
        # Extract data from all files
        extracted_data = []
        for idx, file_path in enumerate(files, 1):
            print(f"\n[{idx}/{len(files)}] Extracting from: {file_path}")
            data = extractor.extract_data(file_path)
            extracted_data.append(data)
            print(f"    ✓ {data.doc_type} extracted")
        
        # Cross-check data
        print("\n🔍 Cross-checking documents...")
        flags = validator.cross_check(extracted_data)
        summary = validator.generate_summary(flags)
        
        # Display results
        print("\n📊 Validation Results:")
        print(f"  Status: {summary['status']}")
        print(f"  Total Issues: {summary['total_issues']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Warnings: {summary['warnings']}")
        
        if summary['error_details']:
            print("\n🔴 Errors:")
            for error in summary['error_details']:
                print(f"  - Field: {error['field']}")
                print(f"    Message: {error['message']}")
        
        if summary['warning_details']:
            print("\n🟡 Warnings:")
            for warning in summary['warning_details']:
                print(f"  - Field: {warning['field']}")
                print(f"    Message: {warning['message']}")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error during cross-check: {e}")
        return None


def example_batch_extract():
    """Example: Extract data from multiple files."""
    print("\n" + "="*60)
    print("Example 3: Batch extract from multiple files")
    print("="*60)
    
    extractor = AIExtractor()
    
    files = [
        "sample_invoice.pdf",
        "sample_packing_list.pdf"
    ]
    
    # Check if files exist
    missing_files = [f for f in files if not os.path.exists(f)]
    if missing_files:
        print(f"\n❌ Files not found: {', '.join(missing_files)}")
        return
    
    try:
        print(f"\nExtracting data from {len(files)} files...")
        data_list = extractor.extract_data_batch(files)
        
        print(f"\n✅ Successfully extracted data from {len(data_list)} files\n")
        
        for idx, data in enumerate(data_list, 1):
            print(f"[{idx}] {data.doc_type}")
            print(f"    BL: {data.bl_no}")
            print(f"    Weight: {data.total_weight} KG")
            print(f"    Packages: {data.total_packages}")
        
        return data_list
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == '__main__':
    print("\n🚀 Logistics Data Extraction - Examples")
    print("=" * 60)
    
    # Uncomment the example you want to run:
    
    # Example 1: Extract single file
    # example_extract_single_file()
    
    # Example 2: Cross-check multiple documents
    # example_cross_check()
    
    # Example 3: Batch extract
    # example_batch_extract()
    
    print("\n" + "="*60)
    print("📝 To run examples:")
    print("   1. Replace 'sample_*.pdf' with your actual files")
    print("   2. Uncomment the example in main section")
    print("   3. Run: python example_usage.py")
    print("="*60)
