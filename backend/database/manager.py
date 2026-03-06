"""
Database module for storing logistics data extraction and validation history.
Uses Supabase (PostgreSQL) for cloud database operations.
"""

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_KEY


class DatabaseManager:
    """Manager for database operations using Supabase."""
    
    def __init__(self):
        """Initialize database manager with Supabase client."""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def create_session(self, session_id: str, initial_status: str = "IN_PROGRESS") -> Dict[str, Any]:
        """Create a new extraction session."""
        data = {
            "session_id": session_id,
            "status": initial_status,
            "created_at": datetime.now().isoformat()
        }
        
        response = self.supabase.table('extraction_sessions').insert(data).execute()
        return response.data[0] if response.data else None
    
    def record_file_upload(
        self,
        session_id: str,
        file_name: str,
        file_type: str,
        document_type: str,
        file_path: str,
        file_size: int,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record a file upload."""
        data = {
            "session_id": session_id,
            "file_name": file_name,
            "file_type": file_type,
            "document_type": document_type,
            "file_path": file_path,
            "file_size": file_size,
            "extracted_data": json.dumps(extracted_data),
            "uploaded_at": datetime.now().isoformat()
        }
        
        response = self.supabase.table('file_uploads').insert(data).execute()
        return response.data[0] if response.data else None
    
    def record_extraction(
        self,
        upload_id: int,
        doc_type: str,
        bl_no: Optional[str],
        invoice_no: Optional[str],
        shipper: Optional[str],
        consignee: Optional[str],
        vessel: Optional[str],
        total_weight: float,
        total_packages: int,
        containers: List[Dict],
        hs_codes: List[str]
    ) -> Dict[str, Any]:
        """Record extracted data."""
        data = {
            "upload_id": upload_id,
            "doc_type": doc_type,
            "bl_no": bl_no,
            "invoice_no": invoice_no,
            "shipper": shipper,
            "consignee": consignee,
            "vessel": vessel,
            "total_weight": total_weight,
            "total_packages": total_packages,
            "containers": json.dumps(containers),
            "hs_codes": json.dumps(hs_codes),
            "extracted_at": datetime.now().isoformat()
        }
        
        response = self.supabase.table('extraction_records').insert(data).execute()
        return response.data[0] if response.data else None
    
    def record_validation(
        self,
        session_id: str,
        check_type: str,
        field_name: str,
        severity: str,
        message: str,
        status: str,
        expected_value: Optional[str] = None,
        actual_values: Optional[Dict] = None,
        recommendation: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record a validation check result."""
        data = {
            "session_id": session_id,
            "check_type": check_type,
            "field_name": field_name,
            "severity": severity,
            "message": message,
            "status": status,
            "expected_value": expected_value,
            "actual_values": json.dumps(actual_values) if actual_values else None,
            "recommendation": recommendation,
            "checked_at": datetime.now().isoformat()
        }
        
        response = self.supabase.table('validation_records').insert(data).execute()
        return response.data[0] if response.data else None
    
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full history of a session."""
        # Get session
        session_response = self.supabase.table('extraction_sessions').select('*').eq('session_id', session_id).execute()
        if not session_response.data:
            return None
        
        extraction_session = session_response.data[0]
        
        # Get uploads
        uploads_response = self.supabase.table('file_uploads').select('*').eq('session_id', session_id).execute()
        uploads = uploads_response.data
        
        # Get validations
        validations_response = self.supabase.table('validation_records').select('*').eq('session_id', session_id).execute()
        validations = validations_response.data
        
        return {
            "session_id": extraction_session["session_id"],
            "created_at": extraction_session["created_at"],
            "status": extraction_session["status"],
            "notes": extraction_session.get("notes"),
            "uploads": [
                {
                    "file_name": u["file_name"],
                    "document_type": u["document_type"],
                    "file_size": u["file_size"],
                    "uploaded_at": u["uploaded_at"],
                    "extracted_data": json.loads(u["extracted_data"]) if u["extracted_data"] else None
                }
                for u in uploads
            ],
            "validations": [
                {
                    "check_type": v["check_type"],
                    "field": v["field_name"],
                    "severity": v["severity"],
                    "message": v["message"],
                    "status": v["status"],
                    "recommendation": v.get("recommendation")
                }
                for v in validations
            ]
        }
    
    def get_total_sessions_count(self) -> int:
        """Get total number of sessions."""
        response = self.supabase.table('extraction_sessions').select('id', count='exact').execute()
        return response.count or 0
    
    def list_sessions_paginated(self, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List recent extraction sessions with pagination and optimized queries.
        Uses a more efficient approach to get file counts.
        """
        # Get sessions with pagination
        response = self.supabase.table('extraction_sessions').select(
            'session_id', 'created_at', 'status'
        ).order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        sessions = response.data
        
        if not sessions:
            return []
        
        # Get all session_ids to batch query
        session_ids = [s['session_id'] for s in sessions]
        
        # Batch query file uploads count for all sessions
        uploads_response = self.supabase.table('file_uploads').select(
            'session_id'
        ).in_('session_id', session_ids).execute()
        
        # Group uploads by session_id
        uploads_by_session = {}
        for upload in uploads_response.data:
            sid = upload['session_id']
            uploads_by_session[sid] = uploads_by_session.get(sid, 0) + 1
        
        # Build result with counts
        result = []
        for s in sessions:
            result.append({
                "session_id": s["session_id"],
                "created_at": s["created_at"],
                "status": s["status"],
                "file_count": uploads_by_session.get(s['session_id'], 0),
                "validation_count": 0  # Can be optimized similarly if needed
            })
        
        return result
    
    def list_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent extraction sessions (legacy method)."""
        return self.list_sessions_paginated(0, limit)
    
    def get_recent_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent sessions with file counts - alias for list_recent_sessions."""
        return self.list_sessions_paginated(0, limit)
    
    def update_session_status(self, session_id: str, status: str, notes: Optional[str] = None):
        """Update session status."""
        data = {"status": status}
        if notes:
            data["notes"] = notes
        
        self.supabase.table('extraction_sessions').update(data).eq('session_id', session_id).execute()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics."""
        sessions_count = self.supabase.table('extraction_sessions').select('id', count='exact').execute()
        uploads_count = self.supabase.table('file_uploads').select('id', count='exact').execute()
        validations_count = self.supabase.table('validation_records').select('id', count='exact').execute()
        
        critical_count = self.supabase.table('validation_records').select('id', count='exact').eq('severity', 'CRITICAL').execute()
        error_count = self.supabase.table('validation_records').select('id', count='exact').eq('severity', 'ERROR').execute()
        
        return {
            "total_sessions": sessions_count.count,
            "total_uploads": uploads_count.count,
            "total_validations": validations_count.count,
            "critical_issues": critical_count.count,
            "error_issues": error_count.count
        }


# Singleton instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager