"""
Validator module for cross-checking logistics data from multiple documents.
Compares Invoice, Packing List, Bill of Lading, and Customs data for consistency.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from ..extractor.ai_extractor import LogisticsData


class FlagStatus(str, Enum):
    """Flag status enumeration."""
    ERROR = "error"
    WARNING = "warning"


class ValidationFlag(BaseModel):
    """Model for validation flags."""
    field: str
    status: FlagStatus
    message: str
    details: Optional[Dict[str, Any]] = None


class CrossCheckValidator:
    """Validator for cross-checking logistics data from multiple documents."""

    # Weight tolerance in KG (5kg)
    WEIGHT_TOLERANCE = 5.0
    
    # Weight unit conversion factors
    UNIT_CONVERSION = {
        'lbs': 0.453592,
        'lb': 0.453592,
        'ton': 1000,
        't': 1000,
        'kg': 1,
        'kgs': 1,
    }

    def __init__(self):
        """Initialize the validator."""
        pass

    def cross_check(self, docs_results: List[LogisticsData]) -> List[ValidationFlag]:
        """
        Cross-check data from multiple documents (Invoice, PL, BL, Customs).
        
        Args:
            docs_results: List of LogisticsData objects from different documents
            
        Returns:
            List of ValidationFlag objects indicating errors and warnings
        """
        flags = []
        
        if not docs_results or len(docs_results) < 2:
            return flags
        
        # Group documents by type
        docs_by_type = {}
        for doc in docs_results:
            doc_type = doc.doc_type.lower()
            if doc_type not in docs_by_type:
                docs_by_type[doc_type] = doc
        
        # Check BL Number consistency (RED ERROR)
        flags.extend(self._check_bl_number(docs_by_type))
        
        # Check Container Numbers consistency (RED ERROR)
        flags.extend(self._check_containers(docs_by_type))
        
        # Check Weight consistency (YELLOW WARNING)
        flags.extend(self._check_weight(docs_by_type))
        
        # Check Package count consistency (YELLOW WARNING)
        flags.extend(self._check_packages(docs_by_type))
        
        # Check Shipper/Consignee consistency (YELLOW WARNING)
        flags.extend(self._check_parties(docs_by_type))
        
        # Check Invoice Number (if exists)
        flags.extend(self._check_invoice_number(docs_by_type))
        
        return flags

    def _check_bl_number(self, docs_by_type: Dict[str, LogisticsData]) -> List[ValidationFlag]:
        """Check if BL number is consistent across documents."""
        flags = []
        bl_numbers = set()
        bl_docs = {}
        
        for doc_type, doc in docs_by_type.items():
            if doc.bl_no:
                bl_numbers.add(doc.bl_no)
                bl_docs[doc_type] = doc.bl_no
        
        # If there are different BL numbers across documents, it's an ERROR
        if len(bl_numbers) > 1:
            flags.append(ValidationFlag(
                field="bl_no",
                status=FlagStatus.ERROR,
                message="BL number không khớp giữa các chứng từ",
                details={
                    "documents": bl_docs,
                    "unique_values": list(bl_numbers)
                }
            ))
        
        return flags

    def _check_containers(self, docs_by_type: Dict[str, LogisticsData]) -> List[ValidationFlag]:
        """Check if container numbers are consistent across documents."""
        flags = []
        container_sets = {}
        
        for doc_type, doc in docs_by_type.items():
            if doc.containers:
                container_nos = {c.container_no for c in doc.containers}
                container_sets[doc_type] = container_nos
        
        # Check if all container sets are identical
        if len(container_sets) > 1:
            all_containers = set()
            for containers in container_sets.values():
                all_containers.update(containers)
            
            # Check for missing containers in any document
            for doc_type, containers in container_sets.items():
                missing = all_containers - containers
                if missing:
                    flags.append(ValidationFlag(
                        field="containers",
                        status=FlagStatus.ERROR,
                        message=f"Container number không khớp. {doc_type} thiếu: {missing}",
                        details={
                            "document": doc_type,
                            "missing_containers": list(missing)
                        }
                    ))
        
        return flags

    def _check_weight(self, docs_by_type: Dict[str, LogisticsData]) -> List[ValidationFlag]:
        """Check if total weight is consistent across documents."""
        flags = []
        weights = {}
        
        for doc_type, doc in docs_by_type.items():
            if doc.total_weight and doc.total_weight > 0:
                weights[doc_type] = doc.total_weight
        
        if len(weights) > 1:
            weights_list = list(weights.values())
            min_weight = min(weights_list)
            max_weight = max(weights_list)
            difference = max_weight - min_weight
            
            if difference > self.WEIGHT_TOLERANCE:
                flags.append(ValidationFlag(
                    field="total_weight",
                    status=FlagStatus.WARNING,
                    message=f"Trọng lượng lệch nhau {difference:.2f}KG (> {self.WEIGHT_TOLERANCE}KG)",
                    details={
                        "weights": weights,
                        "difference": difference,
                        "tolerance": self.WEIGHT_TOLERANCE
                    }
                ))
        
        return flags

    def _check_packages(self, docs_by_type: Dict[str, LogisticsData]) -> List[ValidationFlag]:
        """Check if total package count is consistent across documents."""
        flags = []
        packages = {}
        
        for doc_type, doc in docs_by_type.items():
            if doc.total_packages and doc.total_packages > 0:
                packages[doc_type] = doc.total_packages
        
        if len(packages) > 1:
            packages_set = set(packages.values())
            
            if len(packages_set) > 1:
                flags.append(ValidationFlag(
                    field="total_packages",
                    status=FlagStatus.WARNING,
                    message="Số kiện không khớp giữa các chứng từ",
                    details={
                        "packages": packages,
                        "unique_values": list(packages_set)
                    }
                ))
        
        return flags

    def _check_parties(self, docs_by_type: Dict[str, LogisticsData]) -> List[ValidationFlag]:
        """Check if shipper and consignee information is consistent."""
        flags = []
        shippers = {}
        consignees = {}
        
        for doc_type, doc in docs_by_type.items():
            if doc.shipper:
                shippers[doc_type] = doc.shipper
            if doc.consignee:
                consignees[doc_type] = doc.consignee
        
        # Check shippers
        if len(shippers) > 1:
            shipper_set = set(shippers.values())
            if len(shipper_set) > 1:
                flags.append(ValidationFlag(
                    field="shipper",
                    status=FlagStatus.WARNING,
                    message="Tên người xuất khẩu không khớp giữa các chứng từ",
                    details={
                        "shippers": shippers,
                        "unique_values": list(shipper_set)
                    }
                ))
        
        # Check consignees
        if len(consignees) > 1:
            consignee_set = set(consignees.values())
            if len(consignee_set) > 1:
                flags.append(ValidationFlag(
                    field="consignee",
                    status=FlagStatus.WARNING,
                    message="Tên người nhập khẩu không khớp giữa các chứng từ",
                    details={
                        "consignees": consignees,
                        "unique_values": list(consignee_set)
                    }
                ))
        
        return flags

    def _check_invoice_number(self, docs_by_type: Dict[str, LogisticsData]) -> List[ValidationFlag]:
        """Check if invoice number is present in Invoice document."""
        flags = []
        
        invoice_doc = docs_by_type.get('invoice')
        if invoice_doc and not invoice_doc.invoice_no:
            flags.append(ValidationFlag(
                field="invoice_no",
                status=FlagStatus.WARNING,
                message="Không tìm thấy số hóa đơn trong chứng từ Invoice",
                details={}
            ))
        
        return flags

    def generate_summary(self, flags: List[ValidationFlag]) -> Dict[str, Any]:
        """
        Generate a summary of validation results.
        
        Args:
            flags: List of validation flags
            
        Returns:
            Summary dictionary with error and warning counts
        """
        errors = [f for f in flags if f.status == FlagStatus.ERROR]
        warnings = [f for f in flags if f.status == FlagStatus.WARNING]
        
        return {
            "total_issues": len(flags),
            "errors": len(errors),
            "warnings": len(warnings),
            "error_details": [f.dict() for f in errors],
            "warning_details": [f.dict() for f in warnings],
            "status": "FAILED" if errors else ("WARNING" if warnings else "PASSED")
        }
