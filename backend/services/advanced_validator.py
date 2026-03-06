"""
Advanced Cross-Check Validator for Logistics Data.
Performs intelligent comparison of data from multiple documents (Invoice, PL, BL, Customs).
"""

from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from ..extractor.ai_extractor import LogisticsData, Container


class SeverityLevel(str, Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"      # Must be fixed before processing
    ERROR = "error"             # Should be fixed
    WARNING = "warning"         # Needs attention
    INFO = "info"               # For information


class MatchStatus(str, Enum):
    """Match status for comparison."""
    EXACT_MATCH = "exact_match"
    PARTIAL_MATCH = "partial_match"
    MISMATCH = "mismatch"
    MISSING = "missing"


class ValidationIssue(BaseModel):
    """Model for a validation issue."""
    field: str
    severity: SeverityLevel
    message: str
    documents_involved: List[str]
    expected_value: Optional[Any] = None
    actual_values: Dict[str, Any] = {}
    recommendation: Optional[str] = None


class ComparisonResult(BaseModel):
    """Result of comparing a single field across documents."""
    field: str
    status: MatchStatus
    values: Dict[str, Any]
    percentage_match: float  # 0-100


class AdvancedValidator:
    """Advanced cross-check validator for logistics documents."""

    def __init__(self):
        """Initialize the validator."""
        self.weight_tolerance = 5.0  # kg
        self.volume_tolerance = 0.5  # cbm
        self.quantity_tolerance = 0.05  # 5%

    def validate_documents(self, docs: List[LogisticsData]) -> List[ValidationIssue]:
        """
        Perform comprehensive validation of multiple documents.
        
        Args:
            docs: List of LogisticsData objects
            
        Returns:
            List of ValidationIssue objects
        """
        issues = []
        doc_map = self._map_documents(docs)
        
        # 1. Critical checks - must pass
        issues.extend(self._validate_bl_consistency(doc_map))
        issues.extend(self._validate_container_consistency(doc_map))
        issues.extend(self._validate_seal_consistency(doc_map))
        
        # 2. Error checks - should pass
        issues.extend(self._validate_weight_consistency(doc_map))
        issues.extend(self._validate_package_consistency(doc_map))
        issues.extend(self._validate_shipper_consignee(doc_map))
        issues.extend(self._validate_vessel_consistency(doc_map))
        
        # 3. Warning checks
        issues.extend(self._validate_invoice_number(doc_map))
        issues.extend(self._validate_hs_codes(doc_map))
        
        # 4. Cross-document validation
        issues.extend(self._cross_validate_invoice_vs_pl(doc_map))
        issues.extend(self._cross_validate_bl_vs_pl(doc_map))
        
        return issues

    def _map_documents(self, docs: List[LogisticsData]) -> Dict[str, LogisticsData]:
        """Map documents by type."""
        doc_map = {}
        for doc in docs:
            doc_type = doc.doc_type.lower()
            doc_map[doc_type] = doc
        return doc_map

    # convenience helper for single-document validation
    def validate_single_document(self, doc: LogisticsData) -> List[ValidationIssue]:
        """Validate a single document by wrapping the multi-document validator.

        Args:
            doc: A single LogisticsData instance.

        Returns:
            List of ValidationIssue objects (same format as validate_documents).
        """
        return self.validate_documents([doc])

    # === CRITICAL CHECKS ===

    def _validate_bl_consistency(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if BL number is consistent across all documents."""
        issues = []
        bl_numbers = {}
        
        for doc_type, doc in doc_map.items():
            if doc.bl_no:
                bl_numbers[doc_type] = doc.bl_no
        
        if len(set(bl_numbers.values())) > 1:
            issues.append(ValidationIssue(
                field="bl_no",
                severity=SeverityLevel.CRITICAL,
                message="BL number không khớp giữa các chứng từ. Điều này sẽ gây lỗi trong hệ thống ECUSS.",
                documents_involved=list(bl_numbers.keys()),
                actual_values=bl_numbers,
                recommendation="Kiểm tra lại số vận đơn trên tất cả chứng từ và sửa lỗi trước khi tiếp tục."
            ))
        
        return issues

    def _validate_container_consistency(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if container numbers are consistent across documents."""
        issues = []
        container_sets = {}
        
        for doc_type, doc in doc_map.items():
            if doc.containers:
                container_nos = {c.container_no for c in doc.containers}
                container_sets[doc_type] = container_nos
        
        if len(container_sets) > 1:
            all_containers = set()
            for containers in container_sets.values():
                all_containers.update(containers)
            
            for doc_type, containers in container_sets.items():
                missing = all_containers - containers
                if missing:
                    issues.append(ValidationIssue(
                        field="containers",
                        severity=SeverityLevel.CRITICAL,
                        message=f"Container number thiếu trong {doc_type}: {missing}. Hàng không được ghi chép đầy đủ.",
                        documents_involved=[doc_type],
                        actual_values={"missing_in": doc_type, "missing_containers": list(missing)},
                        recommendation=f"Thêm các container thiếu: {', '.join(missing)}"
                    ))
        
        return issues

    def _validate_seal_consistency(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if seal numbers are consistent."""
        issues = []
        seal_map = {}
        
        for doc_type, doc in doc_map.items():
            if doc.containers:
                for container in doc.containers:
                    if container.seal_no:
                        key = f"{container.container_no}:{container.seal_no}"
                        if key not in seal_map:
                            seal_map[key] = []
                        seal_map[key].append(doc_type)
        
        # Check for seal mismatches
        for doc_type, doc in doc_map.items():
            if doc.containers:
                for container in doc.containers:
                    if container.seal_no:
                        key = f"{container.container_no}:{container.seal_no}"
                        # Check if seal matches in other documents
                        for other_type, other_doc in doc_map.items():
                            if other_type != doc_type and other_doc.containers:
                                other_containers = {c.container_no: c.seal_no for c in other_doc.containers}
                                if container.container_no in other_containers:
                                    if other_containers[container.container_no] != container.seal_no:
                                        issues.append(ValidationIssue(
                                            field="seal_no",
                                            severity=SeverityLevel.CRITICAL,
                                            message=f"Seal mismatch cho container {container.container_no}: {doc_type} có {container.seal_no} nhưng {other_type} có {other_containers[container.container_no]}",
                                            documents_involved=[doc_type, other_type],
                                            actual_values={
                                                doc_type: container.seal_no,
                                                other_type: other_containers[container.container_no]
                                            },
                                            recommendation="Kiểm tra lại số seal trên chứng từ gốc."
                                        ))
        
        return issues

    # === ERROR CHECKS ===

    def _validate_weight_consistency(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if weight is consistent within tolerance."""
        issues = []
        weights = {}
        
        for doc_type, doc in doc_map.items():
            if doc.total_weight and doc.total_weight > 0:
                weights[doc_type] = doc.total_weight
        
        if len(weights) > 1:
            values = list(weights.values())
            min_weight = min(values)
            max_weight = max(values)
            diff = max_weight - min_weight
            
            severity = SeverityLevel.WARNING
            if diff > self.weight_tolerance * 2:  # > 10kg
                severity = SeverityLevel.ERROR
            
            if diff > self.weight_tolerance:
                issues.append(ValidationIssue(
                    field="total_weight",
                    severity=severity,
                    message=f"Trọng lượng lệch {diff:.2f}kg giữa các chứng từ (Tolerance: {self.weight_tolerance}kg)",
                    documents_involved=list(weights.keys()),
                    actual_values=weights,
                    recommendation=f"Kiểm tra lại trọng lượng hàng thực tế hoặc tính toán lại từ Packing List."
                ))
        
        return issues

    def _validate_package_consistency(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if package count matches."""
        issues = []
        packages = {}
        
        for doc_type, doc in doc_map.items():
            if doc.total_packages and doc.total_packages > 0:
                packages[doc_type] = doc.total_packages
        
        if len(packages) > 1:
            if len(set(packages.values())) > 1:
                issues.append(ValidationIssue(
                    field="total_packages",
                    severity=SeverityLevel.ERROR,
                    message=f"Số kiện không khớp giữa các chứng từ",
                    documents_involved=list(packages.keys()),
                    actual_values=packages,
                    recommendation="Kiểm tra lại số lượng kiện trên Packing List và Invoice."
                ))
        
        return issues

    def _validate_shipper_consignee(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if shipper and consignee are consistent."""
        issues = []
        
        shippers = {}
        consignees = {}
        
        for doc_type, doc in doc_map.items():
            if doc.shipper:
                shippers[doc_type] = doc.shipper
            if doc.consignee:
                consignees[doc_type] = doc.consignee
        
        # Check shippers
        if len(set(shippers.values())) > 1:
            issues.append(ValidationIssue(
                field="shipper",
                severity=SeverityLevel.ERROR,
                message="Tên người xuất khẩu (Shipper) không khớp",
                documents_involved=list(shippers.keys()),
                actual_values=shippers,
                recommendation="Sử dụng tên shipper chính thức và kiểm tra lại spelling."
            ))
        
        # Check consignees
        if len(set(consignees.values())) > 1:
            issues.append(ValidationIssue(
                field="consignee",
                severity=SeverityLevel.ERROR,
                message="Tên người nhập khẩu (Consignee) không khớp",
                documents_involved=list(consignees.keys()),
                actual_values=consignees,
                recommendation="Sử dụng tên consignee chính thức và kiểm tra lại spelling."
            ))
        
        return issues

    def _validate_vessel_consistency(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if vessel name is consistent."""
        issues = []
        vessels = {}
        
        for doc_type, doc in doc_map.items():
            if doc.vessel:
                vessels[doc_type] = doc.vessel
        
        if len(vessels) > 1 and len(set(vessels.values())) > 1:
            issues.append(ValidationIssue(
                field="vessel",
                severity=SeverityLevel.WARNING,
                message="Tên tàu không khớp giữa các chứng từ",
                documents_involved=list(vessels.keys()),
                actual_values=vessels,
                recommendation="Kiểm tra lại tên tàu chính thức trên B/L."
            ))
        
        return issues

    # === WARNING CHECKS ===

    def _validate_invoice_number(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if invoice has invoice number."""
        issues = []
        
        invoice_doc = doc_map.get('invoice')
        if invoice_doc and not invoice_doc.invoice_no:
            issues.append(ValidationIssue(
                field="invoice_no",
                severity=SeverityLevel.WARNING,
                message="Không tìm thấy số hóa đơn trong chứng từ Invoice",
                documents_involved=["invoice"],
                recommendation="Kiểm tra lại Invoice gốc hoặc nhập số hóa đơn thủ công."
            ))
        
        return issues

    def _validate_hs_codes(self, doc_map: Dict) -> List[ValidationIssue]:
        """Check if HS codes are present."""
        issues = []
        
        for doc_type, doc in doc_map.items():
            if not doc.hs_code_suggestions or len(doc.hs_code_suggestions) == 0:
                issues.append(ValidationIssue(
                    field="hs_code_suggestions",
                    severity=SeverityLevel.INFO,
                    message=f"Không tìm thấy gợi ý mã HS trong {doc_type}",
                    documents_involved=[doc_type],
                    recommendation="Kiểm tra mô tả hàng hóa để gợi ý mã HS chính xác."
                ))
        
        return issues

    # === CROSS-DOCUMENT VALIDATION ===

    def _cross_validate_invoice_vs_pl(self, doc_map: Dict) -> List[ValidationIssue]:
        """
        Cross-validate Invoice vs Packing List.
        - Check quantity match
        - Check description consistency
        """
        issues = []
        
        invoice = doc_map.get('invoice')
        pl = doc_map.get('packing list') or doc_map.get('pl')
        
        if not invoice or not pl:
            return issues
        
        # Check quantities - with null checks
        if invoice.total_packages and pl.total_packages and invoice.total_packages != pl.total_packages:
            diff_percent = abs(invoice.total_packages - pl.total_packages) / max(invoice.total_packages, pl.total_packages) * 100
            
            if diff_percent > 5:
                issues.append(ValidationIssue(
                    field="total_packages_invoice_vs_pl",
                    severity=SeverityLevel.ERROR,
                    message=f"Số kiện không khớp giữa Invoice ({invoice.total_packages}) và Packing List ({pl.total_packages})",
                    documents_involved=["invoice", "packing list"],
                    actual_values={
                        "invoice": invoice.total_packages,
                        "packing_list": pl.total_packages,
                        "difference_percent": diff_percent
                    },
                    recommendation="Kiểm tra lại số lượng mặt hàng trên Invoice và Packing List."
                ))
        
        return issues

    def _cross_validate_bl_vs_pl(self, doc_map: Dict) -> List[ValidationIssue]:
        """
        Cross-validate BL vs Packing List.
        - Check container consistency
        - Check weight consistency
        """
        issues = []
        
        bl = doc_map.get('bill of lading') or doc_map.get('bl')
        pl = doc_map.get('packing list') or doc_map.get('pl')
        
        if not bl or not pl:
            return issues
        
        # Check if weight calculation is reasonable - with null checks
        if pl.total_packages and pl.total_packages > 0 and bl.total_weight and bl.total_weight > 0:
            weight_per_package = bl.total_weight / pl.total_packages
            
            # Typical weight per carton: 10-50 kg (for common commodities)
            if weight_per_package < 5 or weight_per_package > 100:
                issues.append(ValidationIssue(
                    field="weight_per_package",
                    severity=SeverityLevel.WARNING,
                    message=f"Trọng lượng trung bình per kiện ({weight_per_package:.2f}kg) có vẻ không hợp lý",
                    documents_involved=["bill_of_lading", "packing_list"],
                    actual_values={
                        "total_weight": bl.total_weight,
                        "total_packages": pl.total_packages,
                        "weight_per_package": weight_per_package
                    },
                    recommendation="Kiểm tra lại trọng lượng hoặc số lượng kiện."
                ))
        
        return issues

    def generate_report(self, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Args:
            issues: List of validation issues
            
        Returns:
            Report dictionary
        """
        critical = [i for i in issues if i.severity == SeverityLevel.CRITICAL]
        errors = [i for i in issues if i.severity == SeverityLevel.ERROR]
        warnings = [i for i in issues if i.severity == SeverityLevel.WARNING]
        infos = [i for i in issues if i.severity == SeverityLevel.INFO]
        
        # Determine overall status
        if critical:
            overall_status = "CRITICAL"
        elif errors:
            overall_status = "FAILED"
        elif warnings:
            overall_status = "WARNING"
        else:
            overall_status = "PASSED"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "summary": {
                "critical": len(critical),
                "errors": len(errors),
                "warnings": len(warnings),
                "info": len(infos),
                "total": len(issues)
            },
            "issues": {
                "critical": [i.dict() for i in critical],
                "errors": [i.dict() for i in errors],
                "warnings": [i.dict() for i in warnings],
                "info": [i.dict() for i in infos]
            },
            "recommendations": self._generate_recommendations(issues)
        }

    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        # Critical issues first
        for issue in issues:
            if issue.severity == SeverityLevel.CRITICAL and issue.recommendation:
                recommendations.append(f"[CRITICAL] {issue.recommendation}")
        
        # Then errors
        for issue in issues:
            if issue.severity == SeverityLevel.ERROR and issue.recommendation:
                recommendations.append(f"[ERROR] {issue.recommendation}")
        
        # Then warnings
        for issue in issues:
            if issue.severity == SeverityLevel.WARNING and issue.recommendation:
                recommendations.append(f"[WARNING] {issue.recommendation}")
        
        return recommendations
