"""
eIDAS Compliance Checker

Electronic Identification and Trust Services Regulation (EU) 910/2014 covering:
- Electronic Signatures
- Electronic Seals
- Time Stamps
- Electronic Documents
- Website Authentication
- Qualified Trust Services
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("eidas")
class EIDASChecker(BaseComplianceChecker):
    """eIDAS compliance checker for electronic identification and trust services"""

    def __init__(self):
        super().__init__()
        self.standard_name = "eidas"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all eIDAS compliance checks"""
        return {
            "EIDAS-SIG-1": ComplianceCheck(
                check_id="EIDAS-SIG-1",
                name="Electronic Signature Levels",
                description="Use appropriate signature level for transaction type",
                severity=Severity.HIGH,
                remediation="Use QES for high-value, AdES for medium, simple for low-risk.",
                standard="eidas",
                article="Article 25-26",
                check_type="function_presence",
                required_functions=["create_signature", "verify_signature", "sign_document"],
            ),
            "EIDAS-SIG-2": ComplianceCheck(
                check_id="EIDAS-SIG-2",
                name="Qualified Electronic Signature",
                description="QES required for high-value financial transactions",
                severity=Severity.HIGH,
                remediation="Integrate with QTSP for qualified signatures on high-value contracts.",
                standard="eidas",
                article="Article 25",
                check_type="function_presence",
                required_functions=["qualified_signature", "qes_sign", "verify_qes"],
            ),
            "EIDAS-SEAL-1": ComplianceCheck(
                check_id="EIDAS-SEAL-1",
                name="Electronic Seals",
                description="Use electronic seals for organizational documents",
                severity=Severity.MEDIUM,
                remediation="Implement e-seal for automated document authentication.",
                standard="eidas",
                article="Article 35-36",
                check_type="function_presence",
                required_functions=["create_seal", "verify_seal", "apply_eseal"],
            ),
            "EIDAS-TS-1": ComplianceCheck(
                check_id="EIDAS-TS-1",
                name="Qualified Timestamps",
                description="Use qualified timestamps for audit trails",
                severity=Severity.MEDIUM,
                remediation="Integrate with TSA for qualified timestamps on financial records.",
                standard="eidas",
                article="Article 41-42",
                check_type="function_presence",
                required_functions=["timestamp_document", "verify_timestamp", "qualified_timestamp"],
            ),
            "EIDAS-CERT-1": ComplianceCheck(
                check_id="EIDAS-CERT-1",
                name="QWAC Certificates",
                description="Use QWAC for website authentication (PSD2 TPP)",
                severity=Severity.HIGH,
                remediation="Obtain QWAC from qualified TSP for Open Banking APIs.",
                standard="eidas",
                article="Article 45",
                check_type="function_presence",
                required_functions=["verify_qwac", "validate_certificate", "check_qwac"],
            ),
            "EIDAS-CERT-2": ComplianceCheck(
                check_id="EIDAS-CERT-2",
                name="QSealC Certificates",
                description="Use QSealC for electronic seals",
                severity=Severity.MEDIUM,
                remediation="Obtain QSealC from qualified TSP for e-seals.",
                standard="eidas",
                article="Article 38",
                check_type="documentation",
            ),
            "EIDAS-ID-1": ComplianceCheck(
                check_id="EIDAS-ID-1",
                name="Cross-Border eID Recognition",
                description="Recognize notified eID schemes from other member states",
                severity=Severity.MEDIUM,
                remediation="Implement eIDAS node integration for cross-border eID.",
                standard="eidas",
                article="Article 6",
                check_type="function_presence",
                required_functions=["verify_eidas_id", "cross_border_auth", "eidas_login"],
            ),
            "EIDAS-PRES-1": ComplianceCheck(
                check_id="EIDAS-PRES-1",
                name="Long-Term Preservation",
                description="Ensure long-term validity of signatures",
                severity=Severity.MEDIUM,
                remediation="Implement LTV signatures with embedded timestamps and revocation info.",
                standard="eidas",
                article="Article 34",
                check_type="function_presence",
                required_functions=["ltv_signature", "preserve_signature", "archive_signed"],
            ),
        }


# Export for convenience
EIDAS_CHECKS = EIDASChecker().get_checks()

__all__ = ["EIDASChecker", "EIDAS_CHECKS"]
