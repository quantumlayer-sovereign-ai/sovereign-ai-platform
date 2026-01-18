"""
GDPR Compliance Checker

General Data Protection Regulation (EU) 2016/679 covering:
- Article 5: Principles of Processing
- Article 6: Lawful Basis
- Article 7: Conditions for Consent
- Article 17: Right to Erasure
- Article 20: Data Portability
- Article 25: Data Protection by Design
- Article 33: Breach Notification
- Article 35: Data Protection Impact Assessment
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("gdpr")
class GDPRChecker(BaseComplianceChecker):
    """GDPR compliance checker for EU data protection"""

    def __init__(self):
        super().__init__()
        self.standard_name = "gdpr"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all GDPR compliance checks"""
        return {
            "GDPR-ART5": ComplianceCheck(
                check_id="GDPR-ART5",
                name="Data Minimization",
                description="Personal data must be adequate, relevant, and limited to necessity",
                severity=Severity.HIGH,
                remediation="Review data collection. Collect only data necessary for specified purpose.",
                standard="gdpr",
                article="Article 5(1)(c)",
                patterns=[
                    r"collect_all_data",
                    r"store_everything",
                    r"full_profile_dump",
                ],
            ),
            "GDPR-ART6": ComplianceCheck(
                check_id="GDPR-ART6",
                name="Lawful Basis Documentation",
                description="Processing must have documented lawful basis",
                severity=Severity.CRITICAL,
                remediation="Document lawful basis (consent, contract, legal obligation, vital interests, public task, legitimate interests).",
                standard="gdpr",
                article="Article 6",
                check_type="function_presence",
                required_functions=["verify_lawful_basis", "check_consent", "lawful_basis_check"],
            ),
            "GDPR-ART7": ComplianceCheck(
                check_id="GDPR-ART7",
                name="Consent Requirements",
                description="Consent must be freely given, specific, informed, and unambiguous",
                severity=Severity.HIGH,
                remediation="Implement granular consent with clear purpose specification. Allow withdrawal.",
                standard="gdpr",
                article="Article 7",
                check_type="function_presence",
                required_functions=["get_consent", "withdraw_consent", "consent_management"],
            ),
            "GDPR-ART17": ComplianceCheck(
                check_id="GDPR-ART17",
                name="Right to Erasure",
                description="Data subjects have right to erasure ('right to be forgotten')",
                severity=Severity.CRITICAL,
                remediation="Implement data deletion mechanism. Propagate deletion to processors.",
                standard="gdpr",
                article="Article 17",
                check_type="function_presence",
                required_functions=["delete_personal_data", "erase_user", "right_to_erasure", "gdpr_delete"],
            ),
            "GDPR-ART20": ComplianceCheck(
                check_id="GDPR-ART20",
                name="Data Portability",
                description="Data subjects have right to receive data in machine-readable format",
                severity=Severity.HIGH,
                remediation="Implement data export in JSON/CSV. Enable transfer to other controllers.",
                standard="gdpr",
                article="Article 20",
                check_type="function_presence",
                required_functions=["export_user_data", "data_portability", "download_my_data"],
            ),
            "GDPR-ART25": ComplianceCheck(
                check_id="GDPR-ART25",
                name="Data Protection by Design",
                description="Implement appropriate technical measures by design and default",
                severity=Severity.HIGH,
                remediation="Implement privacy by design: encryption, pseudonymization, access controls.",
                standard="gdpr",
                article="Article 25",
                patterns=[
                    r"privacy\s*=\s*False",
                    r"encryption\s*=\s*False",
                    r"anonymize\s*=\s*False",
                ],
            ),
            "GDPR-ART32": ComplianceCheck(
                check_id="GDPR-ART32",
                name="Security of Processing",
                description="Implement appropriate technical and organizational security measures",
                severity=Severity.HIGH,
                remediation="Implement encryption, pseudonymization, resilience, and regular testing.",
                standard="gdpr",
                article="Article 32",
                patterns=[
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r"ssl\s*=\s*False",
                    r"verify\s*=\s*False",
                    r"secure\s*=\s*False",
                ],
            ),
            "GDPR-ART33": ComplianceCheck(
                check_id="GDPR-ART33",
                name="Breach Notification (72 hours)",
                description="Personal data breach must be notified to supervisory authority within 72 hours",
                severity=Severity.CRITICAL,
                remediation="Implement breach detection and 72-hour notification to DPA.",
                standard="gdpr",
                article="Article 33",
                check_type="function_presence",
                required_functions=["notify_breach", "report_breach", "breach_notification"],
            ),
            "GDPR-ART35": ComplianceCheck(
                check_id="GDPR-ART35",
                name="Data Protection Impact Assessment",
                description="DPIA required for high-risk processing",
                severity=Severity.MEDIUM,
                remediation="Conduct DPIA for profiling, automated decision-making, large-scale processing.",
                standard="gdpr",
                article="Article 35",
                check_type="documentation",
            ),
            "GDPR-ART44": ComplianceCheck(
                check_id="GDPR-ART44",
                name="International Transfer Restrictions",
                description="Transfers outside EU/EEA require appropriate safeguards",
                severity=Severity.CRITICAL,
                remediation="Use SCCs, BCRs, or adequacy decisions for non-EU transfers.",
                standard="gdpr",
                article="Article 44-49",
                patterns=[
                    r'region\s*=\s*["\']us-',  # US regions
                    r"s3\.us-",
                    r"storage\.us-",
                    r"transfer_to_us",
                ],
            ),
            "GDPR-REC78": ComplianceCheck(
                check_id="GDPR-REC78",
                name="Pseudonymization",
                description="Use pseudonymization as technical safeguard",
                severity=Severity.MEDIUM,
                remediation="Implement pseudonymization for personal data. Store identifiers separately.",
                standard="gdpr",
                article="Recital 78",
                check_type="function_presence",
                required_functions=["pseudonymize", "anonymize", "tokenize_pii"],
            ),
        }


# Export for convenience
GDPR_CHECKS = GDPRChecker().get_checks()

__all__ = ["GDPRChecker", "GDPR_CHECKS"]
