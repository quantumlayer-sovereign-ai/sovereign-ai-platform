"""
RBI Compliance Checker

Reserve Bank of India guidelines covering:
- Payment Aggregator Guidelines (2020)
- Data Localization (2018)
- UPI Guidelines
- Customer Protection
- Two-Factor Authentication
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("rbi")
class RBIChecker(BaseComplianceChecker):
    """RBI compliance checker for Indian financial regulations"""

    def __init__(self):
        super().__init__()
        self.standard_name = "rbi"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all RBI compliance checks"""
        return {
            "RBI-DL-1": ComplianceCheck(
                check_id="RBI-DL-1",
                name="Data Localization",
                description="Payment data must be stored in India",
                severity=Severity.CRITICAL,
                remediation="Use Indian data centers (ap-south-1 for AWS, asia-south1 for GCP).",
                standard="rbi",
                patterns=[
                    r'region\s*=\s*["\']us-',  # US AWS regions
                    r'region\s*=\s*["\']eu-',  # EU AWS regions
                    r'region\s*=\s*["\']ap-northeast',  # Asia Pacific (not India)
                    r'region\s*=\s*["\']ap-southeast',  # Asia Pacific (not India)
                    r"\.s3\.us-",  # US S3 buckets
                    r"\.s3\.eu-",  # EU S3 buckets
                    r"storage\.googleapis\.com.*us-",  # GCS US
                    r"storage\.googleapis\.com.*europe-",  # GCS EU
                ],
            ),
            "RBI-DL-2": ComplianceCheck(
                check_id="RBI-DL-2",
                name="Cross-Border Data Transfer",
                description="Payment data must not be transferred outside India",
                severity=Severity.CRITICAL,
                remediation="Process all payment data within India. Only aggregated/anonymized data may be transferred.",
                standard="rbi",
                patterns=[
                    r"cross[_-]?border",
                    r"international[_-]?transfer",
                    r"foreign[_-]?server",
                ],
            ),
            "RBI-PA-1": ComplianceCheck(
                check_id="RBI-PA-1",
                name="Settlement Timeline",
                description="T+1 settlement for payment aggregators",
                severity=Severity.HIGH,
                remediation="Implement T+1 settlement cycle. Document settlement process.",
                standard="rbi",
                check_type="documentation",
            ),
            "RBI-PA-2": ComplianceCheck(
                check_id="RBI-PA-2",
                name="Escrow Account",
                description="Merchant funds must be held in escrow",
                severity=Severity.HIGH,
                remediation="Implement nodal/escrow account for merchant settlements.",
                standard="rbi",
                check_type="documentation",
            ),
            "RBI-SEC-1": ComplianceCheck(
                check_id="RBI-SEC-1",
                name="Two-Factor Authentication",
                description="2FA required for high-value transactions",
                severity=Severity.HIGH,
                remediation="Implement 2FA for transactions above threshold (typically Rs 2000+).",
                standard="rbi",
                check_type="function_presence",
                required_functions=["verify_otp", "send_otp", "two_factor_auth", "validate_otp"],
            ),
            "RBI-UPI-1": ComplianceCheck(
                check_id="RBI-UPI-1",
                name="UPI Transaction Limits",
                description="UPI transaction limits must be enforced",
                severity=Severity.HIGH,
                remediation="Implement per-transaction limit of Rs 1 lakh (Rs 2 lakh for specific categories).",
                standard="rbi",
                patterns=[
                    r"amount\s*>\s*[2-9]\d{5}",  # Amount > 200000
                    r"amount\s*>\s*1\d{6}",  # Amount > 1000000
                ],
            ),
            "RBI-KYC-1": ComplianceCheck(
                check_id="RBI-KYC-1",
                name="KYC Requirements",
                description="KYC verification required for wallet limits",
                severity=Severity.MEDIUM,
                remediation="Implement tiered KYC: Minimum KYC (Rs 10k limit), Full KYC (Rs 2 lakh).",
                standard="rbi",
                check_type="function_presence",
                required_functions=["verify_kyc", "kyc_check", "validate_pan", "verify_aadhaar"],
            ),
            "RBI-CP-1": ComplianceCheck(
                check_id="RBI-CP-1",
                name="Customer Grievance",
                description="Grievance redressal mechanism required",
                severity=Severity.MEDIUM,
                remediation="Implement customer grievance portal with 48-hour acknowledgment.",
                standard="rbi",
                check_type="documentation",
            ),
            "RBI-AML-1": ComplianceCheck(
                check_id="RBI-AML-1",
                name="Transaction Monitoring",
                description="Suspicious transaction monitoring required",
                severity=Severity.HIGH,
                remediation="Implement transaction monitoring for AML/CFT compliance.",
                standard="rbi",
                check_type="function_presence",
                required_functions=["check_suspicious", "aml_check", "transaction_monitoring"],
            ),
        }


# Export for backward compatibility
RBI_CHECKS = RBIChecker().get_checks()

__all__ = ["RBIChecker", "RBI_CHECKS"]
