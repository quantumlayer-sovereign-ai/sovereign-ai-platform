"""
DPDP Act Compliance Checker

Digital Personal Data Protection Act 2023 (India) covering:
- Consent Management
- Purpose Limitation
- Data Minimization
- Storage Limitation
- Data Principal Rights
- Cross-Border Transfer
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("dpdp")
class DPDPChecker(BaseComplianceChecker):
    """DPDP Act compliance checker for Indian data protection"""

    def __init__(self):
        super().__init__()
        self.standard_name = "dpdp"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all DPDP Act compliance checks"""
        return {
            "DPDP-SEC5": ComplianceCheck(
                check_id="DPDP-SEC5",
                name="Consent Management",
                description="Must obtain explicit consent for data processing",
                severity=Severity.HIGH,
                remediation="Implement consent management system with clear purpose specification.",
                standard="dpdp",
                article="Section 5",
                check_type="function_presence",
                required_functions=["get_consent", "record_consent", "consent_management", "verify_consent"],
            ),
            "DPDP-SEC6": ComplianceCheck(
                check_id="DPDP-SEC6",
                name="Lawful Purpose",
                description="Data processing only for specified lawful purposes",
                severity=Severity.HIGH,
                remediation="Document and enforce purpose limitation for all data processing.",
                standard="dpdp",
                article="Section 6",
                check_type="documentation",
            ),
            "DPDP-SEC8": ComplianceCheck(
                check_id="DPDP-SEC8",
                name="Data Minimization",
                description="Collect only necessary personal data",
                severity=Severity.MEDIUM,
                remediation="Review data collection. Remove unnecessary fields. Implement data minimization.",
                standard="dpdp",
                article="Section 8",
                patterns=[
                    r"collect_all",
                    r"store_everything",
                    r"gather_all_data",
                ],
            ),
            "DPDP-SEC11": ComplianceCheck(
                check_id="DPDP-SEC11",
                name="Right to Access",
                description="Data principals have right to access their data",
                severity=Severity.HIGH,
                remediation="Implement data access portal for data principals.",
                standard="dpdp",
                article="Section 11",
                check_type="function_presence",
                required_functions=["get_user_data", "export_user_data", "data_access_request"],
            ),
            "DPDP-SEC12": ComplianceCheck(
                check_id="DPDP-SEC12",
                name="Right to Correction",
                description="Data principals have right to correct their data",
                severity=Severity.MEDIUM,
                remediation="Implement data correction mechanism.",
                standard="dpdp",
                article="Section 12",
                check_type="function_presence",
                required_functions=["update_user_data", "correct_data", "data_correction_request"],
            ),
            "DPDP-SEC13": ComplianceCheck(
                check_id="DPDP-SEC13",
                name="Right to Erasure",
                description="Data principals have right to erasure of data",
                severity=Severity.HIGH,
                remediation="Implement data deletion mechanism with verification.",
                standard="dpdp",
                article="Section 13",
                check_type="function_presence",
                required_functions=["delete_user_data", "erase_data", "data_deletion_request"],
            ),
            "DPDP-SEC16": ComplianceCheck(
                check_id="DPDP-SEC16",
                name="Cross-Border Transfer",
                description="Personal data transfer restrictions",
                severity=Severity.CRITICAL,
                remediation="Only transfer to notified countries. Implement data localization for sensitive data.",
                standard="dpdp",
                article="Section 16",
                patterns=[
                    r"transfer_abroad",
                    r"foreign_storage",
                    r"offshore_backup",
                ],
            ),
            "DPDP-SEC8A": ComplianceCheck(
                check_id="DPDP-SEC8A",
                name="Data Retention",
                description="Data should not be retained beyond necessary period",
                severity=Severity.MEDIUM,
                remediation="Implement data retention policies with automatic purging.",
                standard="dpdp",
                article="Section 8",
                check_type="function_presence",
                required_functions=["purge_old_data", "data_retention_check", "cleanup_expired"],
            ),
            "DPDP-SEC8B": ComplianceCheck(
                check_id="DPDP-SEC8B",
                name="Security Safeguards",
                description="Implement reasonable security safeguards",
                severity=Severity.HIGH,
                remediation="Implement encryption, access controls, and security monitoring.",
                standard="dpdp",
                article="Section 8",
                patterns=[
                    r"password\s*=\s*[\"'][^\"']+[\"']",  # Hardcoded passwords
                    r"encryption\s*=\s*False",
                    r"secure\s*=\s*False",
                ],
            ),
            "DPDP-SEC8C": ComplianceCheck(
                check_id="DPDP-SEC8C",
                name="Breach Notification",
                description="Data breach notification to Board and affected persons",
                severity=Severity.HIGH,
                remediation="Implement breach detection and notification system.",
                standard="dpdp",
                article="Section 8",
                check_type="function_presence",
                required_functions=["report_breach", "notify_breach", "breach_notification"],
            ),
        }


# Export for backward compatibility
DPDP_CHECKS = DPDPChecker().get_checks()

__all__ = ["DPDPChecker", "DPDP_CHECKS"]
