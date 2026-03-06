"""
API routes for PDF extraction endpoints.
"""

import os
import json
import tempfile
import uuid
from flask import Blueprint, request, jsonify
from ..config import app_config, ALLOWED_EXTENSIONS
from ..extractor import CustomsExtractor
from ..extractor.ai_extractor import AIExtractor, LogisticsData
from ..services import CrossCheckValidator
from ..database.manager import get_db_manager
from ..services.advanced_validator import AdvancedValidator, SeverityLevel
from ..services.report_generator import ReportGenerator

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/extract', methods=['POST'])
def extract_pdf():
    """
    API endpoint to extract data from uploaded PDF using AI.
    Accepts a PDF file and returns extracted data as JSON.
    Also saves to database for session tracking.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file extension
    file_ext = file.filename.lower().split('.')[-1]
    if file_ext not in ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp']:
        return jsonify({'error': 'Unsupported file format. Supported: PDF, JPG, PNG, GIF, WEBP'}), 400

    try:
        # Generate session ID
        session_id = str(uuid.uuid4())

        # Initialize services
        db_manager = get_db_manager()
        ai_extractor = AIExtractor()
        validator = AdvancedValidator()
        report_generator = ReportGenerator()

        # Create session in database
        db_manager.create_session(session_id, "IN_PROGRESS")

        # Save file temporarily for processing
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f'.{file_ext}',
            delete=False
        )
        file.save(temp_file.name)

        try:
            # Extract data using AI
            logistics_data = ai_extractor.extract_data(temp_file.name)

            # Convert to dict for JSON storage (English keys)
            # Handle None values properly
            containers_list = logistics_data.containers or []
            hs_code_list = logistics_data.hs_code_suggestions or []
            
            extracted_dict = {
                'doc_type': logistics_data.doc_type,
                'bl_no': logistics_data.bl_no,
                'invoice_no': logistics_data.invoice_no,
                'shipper': logistics_data.shipper,
                'consignee': logistics_data.consignee,
                'vessel': logistics_data.vessel,
                'containers': [
                    {'container_no': c.container_no, 'seal_no': c.seal_no}
                    for c in containers_list
                ],
                'total_weight': logistics_data.total_weight,
                'total_packages': logistics_data.total_packages,
                'hs_code_suggestions': hs_code_list
            }
            
            # Add Vietnamese field names for frontend compatibility
            # Only add fields that have values (not None)
            extracted_dict_vietnamese = {}
            
            if logistics_data.bl_no:
                extracted_dict_vietnamese['Số vận đơn'] = logistics_data.bl_no
            if logistics_data.hs_code_suggestions:
                extracted_dict_vietnamese['Mã số hàng hóa đại diện tờ khai'] = logistics_data.hs_code_suggestions[0]
            if logistics_data.hs_code:
                extracted_dict_vietnamese['Mã số hàng hóa đại diện tờ khai'] = logistics_data.hs_code
            if logistics_data.declaration_office_code:
                extracted_dict_vietnamese['Mã bộ phận xử lý tờ khai'] = logistics_data.declaration_office_code
            if logistics_data.shipper:
                extracted_dict_vietnamese['Người xuất khẩu'] = logistics_data.shipper
            if logistics_data.consignee:
                extracted_dict_vietnamese['Người nhập khẩu'] = logistics_data.consignee
            if logistics_data.vessel:
                extracted_dict_vietnamese['Tên tàu'] = logistics_data.vessel
            if logistics_data.total_weight:
                extracted_dict_vietnamese['Trọng lượng'] = logistics_data.total_weight
            if logistics_data.total_packages:
                extracted_dict_vietnamese['Số lượng'] = logistics_data.total_packages
            if logistics_data.warehouse_location:
                extracted_dict_vietnamese['Địa điểm lưu kho'] = logistics_data.warehouse_location
            if logistics_data.discharge_place:
                extracted_dict_vietnamese['Địa điểm dỡ hàng'] = logistics_data.discharge_place
            if logistics_data.departure_date:
                extracted_dict_vietnamese['Ngày hàng đi'] = logistics_data.departure_date
            if logistics_data.arrival_date:
                extracted_dict_vietnamese['Ngày hàng đến'] = logistics_data.arrival_date
            
            # Merge both dicts
            extracted_dict.update(extracted_dict_vietnamese)

            # Save file upload to database
            db_manager.record_file_upload(
                session_id=session_id,
                file_name=file.filename,
                file_type=file_ext.upper(),
                document_type=logistics_data.doc_type,
                file_path=temp_file.name,  # Temporary path
                file_size=os.path.getsize(temp_file.name),
                extracted_data=extracted_dict
            )

            # Perform validation (single-document wrapper)
            validation_issues = validator.validate_documents([logistics_data])

            # Save validation results
            for issue in validation_issues:
                # map ValidationIssue fields to DB schema
                db_manager.record_validation(
                    session_id=session_id,
                    check_type="auto",  # generic since we don't differentiate types here
                    field_name=issue.field,
                    severity=issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                    message=issue.message,
                    status="",
                    expected_value=issue.expected_value,
                    actual_values=issue.actual_values,
                    recommendation=issue.recommendation
                )

            # Update session status based on severity
            session_status = "PASSED" if not any(i.severity == SeverityLevel.CRITICAL or i.severity == SeverityLevel.ERROR for i in validation_issues) else "WARNING"
            db_manager.update_session_status(session_id, session_status)

            # Generate response
            response_data = {
                'success': True,
                'session_id': session_id,
                'data': extracted_dict,
                'validation': {
                    'issues': [
                        {
                            'field': issue.field,
                            'severity': issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                            'message': issue.message,
                            'documents_involved': issue.documents_involved,
                            'recommendation': issue.recommendation
                        }
                        for issue in validation_issues
                    ],
                    'summary': {
                        'total_issues': len(validation_issues),
                        'critical': len([i for i in validation_issues if i.severity == SeverityLevel.CRITICAL]),
                        'errors': len([i for i in validation_issues if i.severity == SeverityLevel.ERROR]),
                        'warnings': len([i for i in validation_issues if i.severity == SeverityLevel.WARNING]),
                        'info': len([i for i in validation_issues if i.severity == SeverityLevel.INFO])
                    }
                }
            }

            return jsonify(response_data)

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file.name)
            except:
                pass

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/extract-all', methods=['POST'])
def extract_all():
    """
    API endpoint to extract data from multiple logistics documents.

    Accepts:
    - Multiple files (file0, file1, file2, etc.) containing Invoice, PL, BL documents
    - Each file should have a 'doc_type' parameter indicating document type

    Returns:
    - Extracted data from each document
    - Cross-validation flags comparing data across documents
    - Summary of validation results
    """
    try:
        # Check if files are provided
        if len(request.files) == 0:
            return jsonify({'error': 'No files provided'}), 400

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Initialize services
        db_manager = get_db_manager()
        ai_extractor = AIExtractor()
        validator = AdvancedValidator()
        report_generator = ReportGenerator()

        # Create session in database
        db_manager.create_session(session_id, "IN_PROGRESS")

        # Process each file
        extracted_results = []
        temp_files = []

        file_list = list(request.files.values())

        for idx, file in enumerate(file_list):
            if file.filename == '':
                return jsonify({'error': f'File {idx} has no filename'}), 400

            # Validate file extension
            file_ext = file.filename.lower().split('.')[-1]
            if file_ext not in ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp']:
                return jsonify({
                    'error': f'File {idx} has unsupported format. Supported: PDF, JPG, PNG, GIF, WEBP'
                }), 400

            try:
                # Save file to temporary location
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=f'.{file_ext}',
                    delete=False
                )
                file.save(temp_file.name)
                temp_files.append(temp_file.name)

                # Extract data using AI
                logistics_data = ai_extractor.extract_data(temp_file.name)
                extracted_results.append(logistics_data)

                # Convert to dict with Vietnamese fields
                containers_list = logistics_data.containers or []
                hs_code_list = logistics_data.hs_code_suggestions or []
                
                extracted_dict = {
                    'doc_type': logistics_data.doc_type,
                    'bl_no': logistics_data.bl_no,
                    'invoice_no': logistics_data.invoice_no,
                    'shipper': logistics_data.shipper,
                    'consignee': logistics_data.consignee,
                    'vessel': logistics_data.vessel,
                    'containers': [
                        {'container_no': c.container_no, 'seal_no': c.seal_no}
                        for c in containers_list
                    ],
                    'total_weight': logistics_data.total_weight,
                    'total_packages': logistics_data.total_packages,
                    'hs_code_suggestions': hs_code_list,
                    # Additional fields
                    'hs_code': logistics_data.hs_code,
                    'declaration_office_code': logistics_data.declaration_office_code,
                    'warehouse_location': logistics_data.warehouse_location,
                    'discharge_place': logistics_data.discharge_place,
                    'departure_date': logistics_data.departure_date,
                    'arrival_date': logistics_data.arrival_date
                }
                
                # Add Vietnamese field names
                if logistics_data.bl_no:
                    extracted_dict['Số vận đơn'] = logistics_data.bl_no
                if logistics_data.hs_code:
                    extracted_dict['Mã số hàng hóa'] = logistics_data.hs_code
                elif hs_code_list:
                    extracted_dict['Mã số hàng hóa'] = hs_code_list[0]
                if logistics_data.declaration_office_code:
                    extracted_dict['Mã bộ phận xử lý tờ khai'] = logistics_data.declaration_office_code
                if logistics_data.shipper:
                    extracted_dict['Người xuất khẩu'] = logistics_data.shipper
                if logistics_data.consignee:
                    extracted_dict['Người nhập khẩu'] = logistics_data.consignee
                if logistics_data.vessel:
                    extracted_dict['Tên tàu'] = logistics_data.vessel
                if logistics_data.total_weight:
                    extracted_dict['Trọng lượng'] = logistics_data.total_weight
                if logistics_data.total_packages:
                    extracted_dict['Số lượng'] = logistics_data.total_packages
                if logistics_data.warehouse_location:
                    extracted_dict['Địa điểm lưu kho'] = logistics_data.warehouse_location
                if logistics_data.discharge_place:
                    extracted_dict['Địa điểm dỡ hàng'] = logistics_data.discharge_place
                if logistics_data.departure_date:
                    extracted_dict['Ngày hàng đi'] = logistics_data.departure_date
                if logistics_data.arrival_date:
                    extracted_dict['Ngày hàng đến'] = logistics_data.arrival_date

                db_manager.record_file_upload(
                    session_id=session_id,
                    file_name=file.filename,
                    file_type=file_ext.upper(),
                    document_type=logistics_data.doc_type,
                    file_path=temp_file.name,
                    file_size=os.path.getsize(temp_file.name),
                    extracted_data=extracted_dict
                )

            except json.JSONDecodeError as e:
                return jsonify({
                    'error': f'Failed to parse response from file {idx}: {str(e)}'
                }), 500
            except Exception as e:
                return jsonify({
                    'error': f'Failed to extract data from file {idx}: {str(e)}'
                }), 500

        # Perform cross-validation
        validation_issues = validator.validate_documents(extracted_results)

        # Save validation results
        for issue in validation_issues:
            db_manager.record_validation(
                session_id=session_id,
                check_type=getattr(issue, 'check_type', 'auto'),
                field_name=getattr(issue, 'field_name', issue.field),
                severity=str(getattr(issue, 'severity', '')).upper(),
                message=issue.message,
                status=getattr(issue, 'status', ''),
                expected_value=getattr(issue, 'expected_value', None),
                actual_values=getattr(issue, 'actual_values', {}),
                recommendation=getattr(issue, 'recommendation', None)
            )

        # Update session status
        session_status = "PASSED" if not any(str(i.severity).upper() in ["CRITICAL", "ERROR"] for i in validation_issues) else "WARNING"
        db_manager.update_session_status(session_id, session_status)

        # Prepare response with all fields including Vietnamese
        response_documents = []
        for doc in extracted_results:
            containers_list = doc.containers or []
            hs_code_list = doc.hs_code_suggestions or []
            
            doc_dict = {
                'doc_type': doc.doc_type,
                'bl_no': doc.bl_no,
                'invoice_no': doc.invoice_no,
                'shipper': doc.shipper,
                'consignee': doc.consignee,
                'vessel': doc.vessel,
                'containers': [
                    {'container_no': c.container_no, 'seal_no': c.seal_no}
                    for c in containers_list
                ],
                'total_weight': doc.total_weight,
                'total_packages': doc.total_packages,
                'hs_code_suggestions': hs_code_list,
                'hs_code': doc.hs_code,
                'declaration_office_code': doc.declaration_office_code,
                'warehouse_location': doc.warehouse_location,
                'discharge_place': doc.discharge_place,
                'departure_date': doc.departure_date,
                'arrival_date': doc.arrival_date
            }
            
            # Add Vietnamese fields
            if doc.bl_no:
                doc_dict['Số vận đơn'] = doc.bl_no
            if doc.hs_code:
                doc_dict['Mã số hàng hóa'] = doc.hs_code
            elif hs_code_list:
                doc_dict['Mã số hàng hóa'] = hs_code_list[0]
            if doc.declaration_office_code:
                doc_dict['Mã bộ phận xử lý tờ khai'] = doc.declaration_office_code
            if doc.shipper:
                doc_dict['Người xuất khẩu'] = doc.shipper
            if doc.consignee:
                doc_dict['Người nhập khẩu'] = doc.consignee
            if doc.vessel:
                doc_dict['Tên tàu'] = doc.vessel
            if doc.total_weight:
                doc_dict['Trọng lượng'] = doc.total_weight
            if doc.total_packages:
                doc_dict['Số lượng'] = doc.total_packages
            if doc.warehouse_location:
                doc_dict['Địa điểm lưu kho'] = doc.warehouse_location
            if doc.discharge_place:
                doc_dict['Địa điểm dỡ hàng'] = doc.discharge_place
            if doc.departure_date:
                doc_dict['Ngày hàng đi'] = doc.departure_date
            if doc.arrival_date:
                doc_dict['Ngày hàng đến'] = doc.arrival_date
            
            response_documents.append(doc_dict)

        # Prepare response
        response_data = {
            'success': True,
            'session_id': session_id,
            'extracted_documents': response_documents,
            'validation': {
                'issues': [
                    {
                        'check_type': getattr(issue, 'check_type', 'auto'),
                        'field_name': getattr(issue, 'field_name', issue.field),
                        'severity': str(getattr(issue, 'severity', '')).upper(),
                        'message': issue.message,
                        'status': getattr(issue, 'status', ''),
                        'recommendation': getattr(issue, 'recommendation', None)
                    }
                    for issue in validation_issues
                ],
                'summary': {
                    'total_issues': len(validation_issues),
                    'critical': len([i for i in validation_issues if str(getattr(i, 'severity', '')).upper() == 'CRITICAL']),
                    'errors': len([i for i in validation_issues if str(getattr(i, 'severity', '')).upper() == 'ERROR']),
                    'warnings': len([i for i in validation_issues if str(getattr(i, 'severity', '')).upper() == 'WARNING']),
                    'info': len([i for i in validation_issues if str(getattr(i, 'severity', '')).upper() == 'INFO'])
                }
            }
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass


@api_bp.route('/save-comparison', methods=['POST'])
def save_comparison():
    """
    Save user comparison data (ECUSS data vs extracted data).
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        comparison_data = data.get('comparison_data', {})
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        # Save comparison data to database
        db_manager = get_db_manager()
        
        # Update session with comparison data
        for field, value in comparison_data.items():
            db_manager.record_validation(
                session_id=session_id,
                check_type='user_comparison',
                field_name=field,
                severity='INFO',
                message='User entered ECUSS data',
                status='SAVED',
                expected_value=None,
                actual_values={'user_value': value},
                recommendation='Comparison data saved'
            )
        
        return jsonify({
            'success': True,
            'message': 'Comparison saved successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/qc-report/<session_id>', methods=['GET'])
def get_qc_report(session_id):
    """
    Generate Quality Control report for a session.
    """
    try:
        db_manager = get_db_manager()
        session_data = db_manager.get_session_history(session_id)
        
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get all validations for this session
        # This would require adding a method to get validations by session
        
        return jsonify({
            'success': True,
            'session': session_data,
            'report_type': 'quality_control'
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session history and details."""
    try:
        db_manager = get_db_manager()
        session_data = db_manager.get_session_history(session_id)

        if not session_data:
            return jsonify({'error': 'Session not found'}), 404

        return jsonify({
            'success': True,
            'session': session_data
        })

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """
    Get list of recent sessions with pagination.
    
    Query parameters:
    - offset: Number of records to skip (default: 0)
    - limit: Number of records to return (default: 20, max: 100)
    """
    try:
        offset = int(request.args.get('offset', 0))
        limit = min(int(request.args.get('limit', 20)), 100)  # Cap at 100
        
        db_manager = get_db_manager()
        
        # Get total count for pagination info
        total_count = db_manager.get_total_sessions_count()
        
        # Get paginated sessions
        sessions = db_manager.list_sessions_paginated(offset, limit)
        
        # Calculate if there are more records
        has_more = (offset + limit) < total_count

        return jsonify({
            'success': True,
            'sessions': sessions,
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total_count': total_count,
                'has_more': has_more
            }
        })

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics."""
    try:
        db_manager = get_db_manager()
        stats = db_manager.get_statistics()

        return jsonify({
            'success': True,
            'statistics': stats
        })

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/fields', methods=['GET'])
def get_fields():
    """
    Return the list of extraction fields.
    """
    return jsonify({
        'fields': app_config.extraction_keys
    })


@api_bp.route('/document-types', methods=['GET'])
def get_document_types():
    """
    Return available document types.
    """
    from ..config import DOCUMENT_TYPES

    types = []
    for key, value in DOCUMENT_TYPES.items():
        types.append({
            'id': key,
            'name': value.get('name'),
            'field_count': len(value.get('keys', []))
        })

    return jsonify({
        'document_types': types,
        'default': app_config.document_type
    })


@api_bp.route('/config', methods=['GET'])
def get_config():
    """
    Return current configuration.
    """
    return jsonify({
        'document_type': app_config.document_type,
        'document_type_name': app_config.get_document_type_name(),
        'field_count': len(app_config.extraction_keys)
    })

