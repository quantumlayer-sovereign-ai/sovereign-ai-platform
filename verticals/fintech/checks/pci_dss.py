"""
PCI-DSS Compliance Checker

Payment Card Industry Data Security Standard - Global standard
applied across all regions (India, EU, UK).

Requirements covered:
- Requirement 3: Protect stored cardholder data
- Requirement 4: Encrypt transmission of cardholder data
- Requirement 6: Develop and maintain secure systems
- Requirement 8: Identify and authenticate access
- Requirement 10: Track and monitor access
"""

from .base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("pci_dss")
class PCIDSSChecker(BaseComplianceChecker):
    """PCI-DSS compliance checker - Global standard"""

    def __init__(self):
        super().__init__()
        self.standard_name = "pci_dss"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all PCI-DSS compliance checks"""
        return {
            "PCI-3.2": ComplianceCheck(
                check_id="PCI-3.2",
                name="No Storage of Sensitive Auth Data",
                description="CVV/CVC must never be stored after authorization",
                severity=Severity.CRITICAL,
                remediation="Never store CVV/CVC. Use payment gateway tokenization.",
                standard="pci_dss",
                patterns=[
                    r"cvv\s*=",
                    r"cvc\s*=",
                    r"security[_-]?code\s*=",
                    r"\.cvv\s*=",
                    r"card_verification",
                ],
            ),
            "PCI-3.4": ComplianceCheck(
                check_id="PCI-3.4",
                name="Cardholder Data Protection",
                description="Card numbers must be masked or encrypted",
                severity=Severity.CRITICAL,
                remediation="Use tokenization or encryption for card data. Never store full card numbers.",
                standard="pci_dss",
                patterns=[
                    r"\b\d{13,19}\b",  # Potential card numbers
                    r'card[_-]?number\s*=\s*["\'][^"\']+["\']',  # Hardcoded card numbers
                    r"pan\s*=\s*[\"'][0-9]",  # PAN storage
                ],
            ),
            "PCI-4.1": ComplianceCheck(
                check_id="PCI-4.1",
                name="Encryption in Transit",
                description="Use TLS for cardholder data transmission",
                severity=Severity.HIGH,
                remediation="Use HTTPS/TLS 1.2+ for all data transmission. Never disable SSL verification.",
                standard="pci_dss",
                patterns=[
                    r"http://",  # Non-HTTPS URLs
                    r"verify\s*=\s*False",  # Disabled SSL verification
                    r"ssl\s*=\s*False",
                    r"CERT_NONE",  # No certificate verification
                ],
            ),
            "PCI-6.5.1": ComplianceCheck(
                check_id="PCI-6.5.1",
                name="SQL Injection Prevention",
                description="Use parameterized queries to prevent SQL injection",
                severity=Severity.HIGH,
                remediation="Use parameterized queries or ORM. Never concatenate user input into SQL.",
                standard="pci_dss",
                patterns=[
                    r'execute\s*\([^)]*%s',
                    r'f"[^"]*SELECT[^"]*{',
                    r'f"[^"]*INSERT[^"]*{',
                    r'f"[^"]*UPDATE[^"]*{',
                    r'f"[^"]*DELETE[^"]*{',
                    r'\+\s*["\'].*SELECT',
                    r"cursor\.execute\s*\([^)]*\+",
                ],
            ),
            "PCI-6.5.7": ComplianceCheck(
                check_id="PCI-6.5.7",
                name="Cross-Site Scripting (XSS)",
                description="Prevent XSS vulnerabilities",
                severity=Severity.HIGH,
                remediation="Sanitize all user input. Use template engines with auto-escaping.",
                standard="pci_dss",
                patterns=[
                    r"innerHTML\s*=",
                    r"document\.write\s*\(",
                    r"\|safe\s*}}",  # Django/Jinja unsafe marking
                    r"dangerouslySetInnerHTML",  # React unsafe
                ],
            ),
            "PCI-8.2.1": ComplianceCheck(
                check_id="PCI-8.2.1",
                name="Credential Storage",
                description="No hardcoded credentials",
                severity=Severity.HIGH,
                remediation="Use environment variables or secret management (Vault, AWS Secrets Manager).",
                standard="pci_dss",
                patterns=[
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][a-zA-Z0-9]{8,}["\']',
                    r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
                    r'private[_-]?key\s*=\s*["\']',
                ],
            ),
            "PCI-10.2": ComplianceCheck(
                check_id="PCI-10.2",
                name="Audit Logging",
                description="Log all access to cardholder data",
                severity=Severity.MEDIUM,
                remediation="Implement comprehensive audit logging for all financial operations.",
                standard="pci_dss",
                check_type="function_presence",
                required_functions=["audit_log", "log_transaction", "create_audit_trail", "logger.info"],
            ),
            "PCI-6.4.1": ComplianceCheck(
                check_id="PCI-6.4.1",
                name="Separation of Environments",
                description="Production and development must be separated",
                severity=Severity.MEDIUM,
                remediation="Ensure test credentials are not used in production. Use environment-specific configs.",
                standard="pci_dss",
                patterns=[
                    r"ENV\s*=\s*['\"]?dev",
                    r"DEBUG\s*=\s*True",
                    r"test_card",
                    r"sandbox.*production",
                ],
            ),
        }


# Export for backward compatibility
PCI_DSS_CHECKS = PCIDSSChecker().get_checks()

__all__ = ["PCIDSSChecker", "PCI_DSS_CHECKS"]
