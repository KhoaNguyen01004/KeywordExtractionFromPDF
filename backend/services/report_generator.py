"""
Report Generator Module for Logistics Data Validation.
Generates comprehensive quality control reports and comparison tables.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json

from ..extractor.ai_extractor import LogisticsData
from .advanced_validator import ValidationIssue, SeverityLevel


@dataclass
class ComparisonRow:
    """A row in comparison table."""
    field: str
    invoice_value: Optional[str] = None
    pl_value: Optional[str] = None
    bl_value: Optional[str] = None
    status: str = "MATCH"  # MATCH, MISMATCH, MISSING


class ReportGenerator:
    """Generate quality control reports for logistics data."""
    
    def __init__(self):
        """Initialize report generator."""
        pass
    
    def generate_comparison_table(
        self,
        docs: List[LogisticsData],
        issues: List[ValidationIssue]
    ) -> Dict[str, Any]:
        """
        Generate detailed comparison table for all documents.
        
        Args:
            docs: List of extracted logistics data
            issues: List of validation issues
            
        Returns:
            Comparison table structure
        """
        doc_map = self._map_documents(docs)
        
        # Create comparison rows for key fields
        comparison_data = []
        
        # 1. Basic Information
        comparison_data.append(self._compare_field("B/L Number", "bl_no", doc_map, issues))
        comparison_data.append(self._compare_field("Invoice Number", "invoice_no", doc_map, issues))
        
        # 2. Party Information
        comparison_data.append(self._compare_field("Shipper Name", "shipper", doc_map, issues))
        comparison_data.append(self._compare_field("Consignee Name", "consignee", doc_map, issues))
        comparison_data.append(self._compare_field("Vessel Name", "vessel", doc_map, issues))
        
        # 3. Container Information
        comparison_data.append(self._compare_containers(doc_map, issues))
        
        # 4. Cargo Information
        comparison_data.append(self._compare_field("Total Packages", "total_packages", doc_map, issues))
        comparison_data.append(self._compare_field("Total Weight (KG)", "total_weight", doc_map, issues))
        
        # 5. HS Codes
        comparison_data.append(self._compare_hs_codes(doc_map, issues))
        
        return {
            "generated_at": datetime.now().isoformat(),
            "comparison_table": [
                {
                    "field": row.field,
                    "invoice": row.invoice_value,
                    "packing_list": row.pl_value,
                    "bill_of_lading": row.bl_value,
                    "status": row.status
                }
                for row in comparison_data
            ]
        }
    
    def generate_detailed_report(
        self,
        docs: List[LogisticsData],
        issues: List[ValidationIssue],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive quality control report.
        
        Args:
            docs: List of extracted logistics data
            issues: List of validation issues
            session_id: Unique session ID
            
        Returns:
            Complete report dictionary
        """
        doc_map = self._map_documents(docs)
        comparison = self.generate_comparison_table(docs, issues)
        
        # Determine overall status
        critical_issues = [i for i in issues if i.severity == SeverityLevel.CRITICAL]
        error_issues = [i for i in issues if i.severity == SeverityLevel.ERROR]
        warning_issues = [i for i in issues if i.severity == SeverityLevel.WARNING]
        
        if critical_issues:
            overall_status = "CRITICAL"
            overall_message = "Có lỗi quan trọng. Không thể tiếp tục xử lý."
        elif error_issues:
            overall_status = "FAILED"
            overall_message = "Có lỗi cần sửa chữa trước khi tiếp tục."
        elif warning_issues:
            overall_status = "WARNING"
            overall_message = "Có cảnh báo cần kiểm tra."
        else:
            overall_status = "PASSED"
            overall_message = "Dữ liệu hợp lệ và sẵn sàng xử lý."
        
        return {
            "report_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "overall_status": overall_status,
            "overall_message": overall_message,
            
            # Executive Summary
            "summary": {
                "total_documents": len(docs),
                "document_types": [d.doc_type for d in docs],
                "total_issues": len(issues),
                "critical_count": len(critical_issues),
                "error_count": len(error_issues),
                "warning_count": len(warning_issues),
                "ready_for_ecuss": len(critical_issues) == 0
            },
            
            # Document Details
            "documents": [
                {
                    "document_type": doc.doc_type,
                    "bl_number": doc.bl_no,
                    "invoice_number": doc.invoice_no,
                    "shipper": doc.shipper,
                    "consignee": doc.consignee,
                    "vessel": doc.vessel,
                    "total_weight": doc.total_weight,
                    "total_packages": doc.total_packages,
                    "container_count": len(doc.containers),
                    "containers": [
                        {
                            "number": c.container_no,
                            "seal": c.seal_no
                        }
                        for c in doc.containers
                    ],
                    "hs_codes": doc.hs_code_suggestions
                }
                for doc in docs
            ],
            
            # Comparison Table
            "comparison": comparison,
            
            # Issues Breakdown
            "issues_breakdown": {
                "critical": [self._issue_to_dict(i) for i in critical_issues],
                "errors": [self._issue_to_dict(i) for i in error_issues],
                "warnings": [self._issue_to_dict(i) for i in warning_issues]
            },
            
            # Quality Metrics
            "quality_metrics": {
                "data_completeness": self._calculate_completeness(docs),
                "consistency_score": self._calculate_consistency_score(issues),
                "confidence_level": self._calculate_confidence(docs, issues)
            },
            
            # Recommendations
            "recommendations": self._generate_detailed_recommendations(issues),
            
            # Action Items
            "action_items": self._generate_action_items(critical_issues, error_issues),
            
            # Next Steps
            "next_steps": self._generate_next_steps(overall_status)
        }
    
    def generate_html_report(
        self,
        report: Dict[str, Any]
    ) -> str:
        """
        Generate HTML version of the report for viewing in browser.
        
        Args:
            report: Report dictionary from generate_detailed_report
            
        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Logistics Data Validation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        
        .header {{ border-bottom: 3px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 28px; color: #2c3e50; margin-bottom: 10px; }}
        .header .meta {{ color: #7f8c8d; font-size: 14px; }}
        
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        .status-critical {{ background: #e74c3c; color: white; }}
        .status-failed {{ background: #e67e22; color: white; }}
        .status-warning {{ background: #f39c12; color: white; }}
        .status-passed {{ background: #27ae60; color: white; }}
        
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #ecf0f1; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .summary-card h3 {{ color: #2c3e50; margin-bottom: 10px; font-size: 14px; text-transform: uppercase; }}
        .summary-card .value {{ font-size: 32px; font-weight: bold; color: #2c3e50; }}
        
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; font-weight: bold; }}
        td {{ padding: 12px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f9f9f9; }}
        
        .match {{ background: #d5f4e6; color: #27ae60; }}
        .mismatch {{ background: #fadbd8; color: #e74c3c; }}
        .missing {{ background: #fceaa3; color: #f39c12; }}
        
        .issues-section {{ margin-top: 30px; }}
        .issues-section h2 {{ color: #2c3e50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
        
        .issue-item {{ 
            padding: 15px; 
            margin-bottom: 10px; 
            border-left: 4px solid #3498db; 
            background: #ecf0f1;
            border-radius: 4px;
        }}
        .issue-critical {{ border-left-color: #e74c3c; background: #fadbd8; }}
        .issue-error {{ border-left-color: #e67e22; background: #fdebd0; }}
        .issue-warning {{ border-left-color: #f39c12; background: #fceaa3; }}
        
        .issue-item .field {{ font-weight: bold; color: #2c3e50; margin-bottom: 5px; }}
        .issue-item .message {{ color: #34495e; margin-bottom: 8px; }}
        .issue-item .recommendation {{ color: #16a085; font-style: italic; margin-top: 8px; }}
        
        .action-items {{ 
            background: #fff3cd; 
            border: 1px solid #ffc107;
            padding: 20px;
            border-radius: 4px;
            margin-top: 30px;
        }}
        .action-items h3 {{ color: #856404; margin-bottom: 15px; }}
        .action-items ol {{ margin-left: 20px; }}
        .action-items li {{ margin-bottom: 10px; color: #856404; }}
        
        .footer {{ 
            margin-top: 40px; 
            padding-top: 20px; 
            border-top: 1px solid #ecf0f1; 
            color: #7f8c8d; 
            font-size: 12px; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Logistics Data Validation Report</h1>
            <div class="meta">
                <p>Report ID: {report['report_id']}</p>
                <p>Generated: {report['generated_at']}</p>
            </div>
        </div>
        
        <div class="status-badge status-{report['overall_status'].lower()}">
            {report['overall_status']}: {report['overall_message']}
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Documents</h3>
                <div class="value">{report['summary']['total_documents']}</div>
            </div>
            <div class="summary-card">
                <h3>Total Issues</h3>
                <div class="value">{report['summary']['total_issues']}</div>
            </div>
            <div class="summary-card">
                <h3>Critical Issues</h3>
                <div class="value" style="color: #e74c3c;">{report['summary']['critical_count']}</div>
            </div>
            <div class="summary-card">
                <h3>Ready for ECUSS</h3>
                <div class="value">{'✓ YES' if report['summary']['ready_for_ecuss'] else '✗ NO'}</div>
            </div>
        </div>
        
        <h2 style="color: #2c3e50; margin-top: 30px;">Comparison Table</h2>
        <table>
            <thead>
                <tr>
                    <th>Field</th>
                    <th>Invoice</th>
                    <th>Packing List</th>
                    <th>Bill of Lading</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for row in report['comparison']['comparison_table']:
            status_class = "match" if row['status'] == "MATCH" else "mismatch"
            html += f"""
                <tr>
                    <td><strong>{row['field']}</strong></td>
                    <td>{row['invoice'] or '-'}</td>
                    <td>{row['packing_list'] or '-'}</td>
                    <td>{row['bill_of_lading'] or '-'}</td>
                    <td class="{status_class}">{row['status']}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        # Issues section
        if report['issues_breakdown']['critical']:
            html += """
            <div class="issues-section">
                <h2>🔴 Critical Issues</h2>
            """
            for issue in report['issues_breakdown']['critical']:
                html += f"""
                <div class="issue-item issue-critical">
                    <div class="field">{issue['field']}</div>
                    <div class="message">{issue['message']}</div>
                    <div class="recommendation">💡 {issue['recommendation']}</div>
                </div>
                """
            html += "</div>"
        
        if report['issues_breakdown']['errors']:
            html += """
            <div class="issues-section">
                <h2>🟠 Errors</h2>
            """
            for issue in report['issues_breakdown']['errors']:
                html += f"""
                <div class="issue-item issue-error">
                    <div class="field">{issue['field']}</div>
                    <div class="message">{issue['message']}</div>
                    <div class="recommendation">💡 {issue['recommendation']}</div>
                </div>
                """
            html += "</div>"
        
        if report['issues_breakdown']['warnings']:
            html += """
            <div class="issues-section">
                <h2>🟡 Warnings</h2>
            """
            for issue in report['issues_breakdown']['warnings']:
                html += f"""
                <div class="issue-item issue-warning">
                    <div class="field">{issue['field']}</div>
                    <div class="message">{issue['message']}</div>
                    <div class="recommendation">💡 {issue['recommendation']}</div>
                </div>
                """
            html += "</div>"
        
        # Action items
        if report['action_items']:
            html += f"""
            <div class="action-items">
                <h3>📌 Action Items</h3>
                <ol>
            """
            for item in report['action_items']:
                html += f"<li>{item}</li>"
            html += """
                </ol>
            </div>
            """
        
        # Footer
        html += f"""
        <div class="footer">
            <p>This report was automatically generated by Logistics Data Validation System.</p>
            <p>Please verify all issues and recommendations before processing documents in ECUSS.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def export_to_json(self, report: Dict[str, Any], file_path: str):
        """Export report to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def export_to_html(self, report: Dict[str, Any], file_path: str):
        """Export report to HTML file."""
        html_content = self.generate_html_report(report)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    # === Helper Methods ===
    
    def _map_documents(self, docs: List[LogisticsData]) -> Dict[str, LogisticsData]:
        """Map documents by type."""
        doc_map = {}
        for doc in docs:
            doc_type_key = self._normalize_doc_type(doc.doc_type)
            doc_map[doc_type_key] = doc
        return doc_map
    
    def _normalize_doc_type(self, doc_type: str) -> str:
        """Normalize document type for comparison."""
        normalized = doc_type.lower()
        if 'invoice' in normalized:
            return 'invoice'
        elif 'packing' in normalized or 'pl' in normalized:
            return 'packing_list'
        elif 'bill' in normalized or 'bl' in normalized or 'lading' in normalized:
            return 'bill_of_lading'
        elif 'customs' in normalized or 'declaration' in normalized:
            return 'customs'
        return normalized
    
    def _compare_field(
        self,
        field_label: str,
        field_name: str,
        doc_map: Dict,
        issues: List[ValidationIssue]
    ) -> ComparisonRow:
        """Compare a single field across documents."""
        invoice = doc_map.get('invoice', {})
        pl = doc_map.get('packing_list', {})
        bl = doc_map.get('bill_of_lading', {})
        
        inv_val = str(getattr(invoice, field_name, None)) if hasattr(invoice, field_name) else None
        pl_val = str(getattr(pl, field_name, None)) if hasattr(pl, field_name) else None
        bl_val = str(getattr(bl, field_name, None)) if hasattr(bl, field_name) else None
        
        # Determine status
        values = [v for v in [inv_val, pl_val, bl_val] if v and v != 'None']
        if len(set(values)) <= 1:
            status = "MATCH"
        else:
            status = "MISMATCH"
        
        return ComparisonRow(
            field=field_label,
            invoice_value=inv_val,
            pl_value=pl_val,
            bl_value=bl_val,
            status=status
        )
    
    def _compare_containers(self, doc_map: Dict, issues: List[ValidationIssue]) -> ComparisonRow:
        """Compare container information."""
        containers_text = []
        for doc_type, doc in doc_map.items():
            if doc.containers:
                containers_text.append(
                    f"{', '.join([c.container_no for c in doc.containers])}"
                )
        
        status = "MATCH" if len(set(containers_text)) <= 1 else "MISMATCH"
        
        return ComparisonRow(
            field="Containers",
            invoice_value=containers_text[0] if len(containers_text) > 0 else None,
            pl_value=containers_text[1] if len(containers_text) > 1 else None,
            bl_value=containers_text[2] if len(containers_text) > 2 else None,
            status=status
        )
    
    def _compare_hs_codes(self, doc_map: Dict, issues: List[ValidationIssue]) -> ComparisonRow:
        """Compare HS codes."""
        hs_texts = []
        for doc_type, doc in doc_map.items():
            if doc.hs_code_suggestions:
                hs_texts.append(", ".join(doc.hs_code_suggestions))
        
        status = "MATCH" if len(set(hs_texts)) <= 1 else "MISMATCH"
        
        return ComparisonRow(
            field="HS Codes",
            invoice_value=hs_texts[0] if len(hs_texts) > 0 else None,
            pl_value=hs_texts[1] if len(hs_texts) > 1 else None,
            bl_value=hs_texts[2] if len(hs_texts) > 2 else None,
            status=status
        )
    
    def _issue_to_dict(self, issue: ValidationIssue) -> Dict[str, Any]:
        """Convert ValidationIssue to dictionary."""
        return {
            "field": issue.field,
            "severity": issue.severity,
            "message": issue.message,
            "documents": issue.documents_involved,
            "recommendation": issue.recommendation
        }
    
    def _calculate_completeness(self, docs: List[LogisticsData]) -> float:
        """Calculate data completeness percentage."""
        total_fields = 0
        filled_fields = 0
        
        for doc in docs:
            fields = [
                doc.doc_type, doc.bl_no, doc.invoice_no,
                doc.shipper, doc.consignee, doc.vessel,
                doc.total_weight, doc.total_packages,
                len(doc.containers) > 0
            ]
            total_fields += len(fields)
            filled_fields += sum(1 for f in fields if f)
        
        return (filled_fields / total_fields * 100) if total_fields > 0 else 0
    
    def _calculate_consistency_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate consistency score based on issues."""
        if not issues:
            return 100.0
        
        critical = len([i for i in issues if i.severity == SeverityLevel.CRITICAL])
        errors = len([i for i in issues if i.severity == SeverityLevel.ERROR])
        warnings = len([i for i in issues if i.severity == SeverityLevel.WARNING])
        
        score = 100 - (critical * 10 + errors * 5 + warnings * 1)
        return max(0, min(100, score))
    
    def _calculate_confidence(self, docs: List[LogisticsData], issues: List[ValidationIssue]) -> str:
        """Determine confidence level."""
        critical = len([i for i in issues if i.severity == SeverityLevel.CRITICAL])
        errors = len([i for i in issues if i.severity == SeverityLevel.ERROR])
        
        if critical > 0:
            return "LOW"
        elif errors > 0:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _generate_detailed_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate detailed recommendations from issues."""
        recommendations = []
        
        for issue in sorted(issues, key=lambda x: x.severity.value):
            if issue.recommendation:
                prefix = f"[{issue.severity.upper()}]"
                recommendations.append(f"{prefix} {issue.recommendation}")
        
        return recommendations
    
    def _generate_action_items(
        self,
        critical_issues: List[ValidationIssue],
        error_issues: List[ValidationIssue]
    ) -> List[str]:
        """Generate prioritized action items."""
        actions = []
        
        if critical_issues:
            actions.append(f"Fix {len(critical_issues)} critical issue(s) immediately")
            for issue in critical_issues:
                actions.append(f"  - {issue.message}")
        
        if error_issues:
            actions.append(f"Correct {len(error_issues)} error(s)")
        
        actions.append("Review comparison table for any mismatches")
        actions.append("Verify all document signatures and stamps")
        actions.append("Submit corrected documents to customs for processing")
        
        return actions
    
    def _generate_next_steps(self, overall_status: str) -> List[str]:
        """Generate next steps based on overall status."""
        if overall_status == "CRITICAL":
            return [
                "1. Contact vendor/supplier to correct document errors",
                "2. Request updated Invoice, PL, and B/L",
                "3. Re-submit documents for validation",
                "4. DO NOT proceed with ECUSS processing"
            ]
        elif overall_status == "FAILED":
            return [
                "1. Manually correct the identified errors",
                "2. Update documents in the system",
                "3. Re-validate before ECUSS submission",
                "4. Ensure all corrections are made before proceeding"
            ]
        elif overall_status == "WARNING":
            return [
                "1. Review warning items carefully",
                "2. Verify data with physical documents",
                "3. If confident, proceed to ECUSS with caution",
                "4. Keep documentation for audit trail"
            ]
        else:  # PASSED
            return [
                "1. ✓ All validations passed",
                "2. Ready to proceed with ECUSS submission",
                "3. Ensure customs clearance is obtained",
                "4. Monitor shipment status in ECUSS"
            ]
