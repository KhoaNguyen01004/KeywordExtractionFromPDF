"""Test the NoneType fix in validators."""
import sys
sys.path.insert(0, 'd:/Code/PhuongNghiHelp/KeywordExtractionFromPDF')

try:
    from backend.services.advanced_validator import AdvancedValidator
    from backend.services.validator import CrossCheckValidator
    print('Import successful!')
    
    # Test with None values
    from backend.extractor.ai_extractor import LogisticsData
    
    # Create test data with None values
    test_doc = LogisticsData(
        doc_type="Invoice",
        bl_no=None,
        invoice_no="INV001",
        shipper="Test Shipper",
        consignee="Test Consignee",
        vessel=None,
        containers=[],
        total_weight=None,  # This was causing the error
        total_packages=None,  # This was causing the error
        hs_code_suggestions=[]
    )
    
    # Test the validator
    validator = AdvancedValidator()
    issues = validator.validate_documents([test_doc])
    print(f'Validation completed! Found {len(issues)} issues')
    print('NoneType fix working correctly!')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
