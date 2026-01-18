"""
UK GDPR Compliance Checker

UK General Data Protection Regulation (Data Protection Act 2018) covering:
- Lawful Processing
- Data Subject Rights
- Security Requirements
- International Transfers (post-Brexit)
- ICO Breach Notification
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("uk_gdpr")
class UKGDPRChecker(BaseComplianceChecker):
    """UK GDPR compliance checker for UK data protection"""

    def __init__(self):
        super().__init__()
        self.standard_name = "uk_gdpr"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all UK GDPR compliance checks"""
        return {
            "UKGDPR-ART5": ComplianceCheck(
                check_id="UKGDPR-ART5",
                name="Data Processing Principles",
                description="Personal data must be processed lawfully, fairly, and transparently",
                severity=Severity.HIGH,
                remediation="Ensure all processing meets UK GDPR principles.",
                standard="uk_gdpr",
                article="Article 5 UK GDPR",
                check_type="documentation",
            ),
            "UKGDPR-ART6": ComplianceCheck(
                check_id="UKGDPR-ART6",
                name="Lawful Basis",
                description="Processing must have valid lawful basis under UK GDPR",
                severity=Severity.CRITICAL,
                remediation="Document lawful basis. Note UK-specific legitimate interests provisions.",
                standard="uk_gdpr",
                article="Article 6 UK GDPR",
                check_type="function_presence",
                required_functions=["verify_lawful_basis", "check_consent", "lawful_basis_check"],
            ),
            "UKGDPR-ART17": ComplianceCheck(
                check_id="UKGDPR-ART17",
                name="Right to Erasure",
                description="Data subjects have right to erasure",
                severity=Severity.CRITICAL,
                remediation="Implement data deletion with verification.",
                standard="uk_gdpr",
                article="Article 17 UK GDPR",
                check_type="function_presence",
                required_functions=["delete_personal_data", "erase_user", "right_to_erasure"],
            ),
            "UKGDPR-ART20": ComplianceCheck(
                check_id="UKGDPR-ART20",
                name="Data Portability",
                description="Data subjects have right to data portability",
                severity=Severity.HIGH,
                remediation="Implement data export in machine-readable format.",
                standard="uk_gdpr",
                article="Article 20 UK GDPR",
                check_type="function_presence",
                required_functions=["export_user_data", "data_portability", "download_my_data"],
            ),
            "UKGDPR-ART33": ComplianceCheck(
                check_id="UKGDPR-ART33",
                name="ICO Breach Notification",
                description="Notify ICO of personal data breach within 72 hours",
                severity=Severity.CRITICAL,
                remediation="Implement breach detection and notification to ICO.",
                standard="uk_gdpr",
                article="Article 33 UK GDPR",
                check_type="function_presence",
                required_functions=["notify_ico", "report_breach", "breach_notification"],
            ),
            "UKGDPR-ART44": ComplianceCheck(
                check_id="UKGDPR-ART44",
                name="International Transfer Restrictions",
                description="Transfers outside UK require appropriate safeguards",
                severity=Severity.CRITICAL,
                remediation="Use UK adequacy regulations, IDTAs, or SCCs for international transfers.",
                standard="uk_gdpr",
                article="Article 44-49 UK GDPR",
                patterns=[
                    r'region\s*=\s*["\'](?!eu-|uk-)',  # Non-UK/EU regions
                ],
            ),
            "UKGDPR-IDTA": ComplianceCheck(
                check_id="UKGDPR-IDTA",
                name="International Data Transfer Agreement",
                description="Use IDTA or UK Addendum for transfers",
                severity=Severity.HIGH,
                remediation="Implement IDTA for transfers to non-adequate countries.",
                standard="uk_gdpr",
                article="UK IDTA",
                check_type="documentation",
            ),
            "UKGDPR-SEC": ComplianceCheck(
                check_id="UKGDPR-SEC",
                name="Security of Processing",
                description="Implement appropriate technical and organizational measures",
                severity=Severity.HIGH,
                remediation="Implement encryption, access controls, and security monitoring.",
                standard="uk_gdpr",
                article="Article 32 UK GDPR",
                patterns=[
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r"ssl\s*=\s*False",
                    r"verify\s*=\s*False",
                    r"encryption\s*=\s*False",
                ],
            ),
        }


# Export for convenience
UK_GDPR_CHECKS = UKGDPRChecker().get_checks()

__all__ = ["UKGDPRChecker", "UK_GDPR_CHECKS"]
