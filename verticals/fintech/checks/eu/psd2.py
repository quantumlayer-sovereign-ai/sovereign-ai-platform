"""
PSD2 Compliance Checker

Payment Services Directive 2 (EU) 2015/2366 covering:
- Strong Customer Authentication (SCA)
- Dynamic Linking
- Open Banking APIs for TPPs
- Transaction Risk Analysis
- SCA Exemptions
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("psd2")
class PSD2Checker(BaseComplianceChecker):
    """PSD2 compliance checker for EU payment services"""

    def __init__(self):
        super().__init__()
        self.standard_name = "psd2"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all PSD2 compliance checks"""
        return {
            "PSD2-SCA-1": ComplianceCheck(
                check_id="PSD2-SCA-1",
                name="Strong Customer Authentication",
                description="SCA required: 2 of 3 factors (knowledge, possession, inherence)",
                severity=Severity.CRITICAL,
                remediation="Implement SCA with at least 2 independent elements from different categories.",
                standard="psd2",
                article="Article 97",
                check_type="function_presence",
                required_functions=[
                    "verify_sca", "strong_customer_auth", "two_factor_auth",
                    "biometric_verify", "sca_check"
                ],
            ),
            "PSD2-SCA-2": ComplianceCheck(
                check_id="PSD2-SCA-2",
                name="Dynamic Linking",
                description="Authentication code must be linked to amount and payee",
                severity=Severity.CRITICAL,
                remediation="Generate authentication code dynamically linked to specific amount and recipient.",
                standard="psd2",
                article="Article 97(2)",
                patterns=[
                    r"static_otp",
                    r"reusable_token",
                    r"fixed_auth_code",
                ],
            ),
            "PSD2-SCA-3": ComplianceCheck(
                check_id="PSD2-SCA-3",
                name="Independence of Elements",
                description="SCA elements must be independent - breach of one doesn't compromise others",
                severity=Severity.HIGH,
                remediation="Ensure authentication factors are truly independent (different channels/methods).",
                standard="psd2",
                article="RTS Article 9",
                check_type="documentation",
            ),
            "PSD2-API-1": ComplianceCheck(
                check_id="PSD2-API-1",
                name="Open Banking API for TPPs",
                description="ASPSPs must provide API access to AISPs and PISPs",
                severity=Severity.HIGH,
                remediation="Implement Open Banking APIs compliant with Berlin Group or OBIE standards.",
                standard="psd2",
                article="Article 66-67",
                check_type="function_presence",
                required_functions=["get_account_info", "initiate_payment", "verify_tpp"],
            ),
            "PSD2-API-2": ComplianceCheck(
                check_id="PSD2-API-2",
                name="TPP Registration Verification",
                description="Verify TPP registration with competent authority",
                severity=Severity.HIGH,
                remediation="Verify TPP eIDAS certificates and registration before granting access.",
                standard="psd2",
                article="Article 19",
                check_type="function_presence",
                required_functions=["verify_tpp_certificate", "check_tpp_registration", "validate_qwac"],
            ),
            "PSD2-EXEMPT-1": ComplianceCheck(
                check_id="PSD2-EXEMPT-1",
                name="SCA Exemption - Low Value",
                description="SCA exemption for low-value remote transactions (<€30)",
                severity=Severity.MEDIUM,
                remediation="Implement exemption with cumulative €100 or 5 transaction limit.",
                standard="psd2",
                article="RTS Article 16",
                check_type="documentation",
            ),
            "PSD2-EXEMPT-2": ComplianceCheck(
                check_id="PSD2-EXEMPT-2",
                name="SCA Exemption - TRA",
                description="Transaction Risk Analysis exemption based on fraud rates",
                severity=Severity.MEDIUM,
                remediation="Implement real-time fraud scoring. Document TRA methodology.",
                standard="psd2",
                article="RTS Article 18",
                check_type="function_presence",
                required_functions=["transaction_risk_analysis", "fraud_score", "tra_exemption"],
            ),
            "PSD2-EXEMPT-3": ComplianceCheck(
                check_id="PSD2-EXEMPT-3",
                name="SCA Exemption - Trusted Beneficiary",
                description="Trusted beneficiary list exemption",
                severity=Severity.MEDIUM,
                remediation="Implement trusted beneficiary list with SCA at addition.",
                standard="psd2",
                article="RTS Article 13",
                check_type="function_presence",
                required_functions=["add_trusted_beneficiary", "check_trusted", "whitelist_payee"],
            ),
            "PSD2-FRAUD-1": ComplianceCheck(
                check_id="PSD2-FRAUD-1",
                name="Fraud Monitoring",
                description="Real-time transaction monitoring for fraud detection",
                severity=Severity.HIGH,
                remediation="Implement real-time fraud detection with behavioral analysis.",
                standard="psd2",
                article="Article 95",
                check_type="function_presence",
                required_functions=["detect_fraud", "fraud_check", "transaction_monitoring"],
            ),
            "PSD2-REFUND-1": ComplianceCheck(
                check_id="PSD2-REFUND-1",
                name="Refund Rights",
                description="Immediate refund for unauthorized transactions",
                severity=Severity.HIGH,
                remediation="Implement immediate refund mechanism for unauthorized transactions.",
                standard="psd2",
                article="Article 73",
                check_type="function_presence",
                required_functions=["process_refund", "unauthorized_refund", "dispute_transaction"],
            ),
        }


# Export for convenience
PSD2_CHECKS = PSD2Checker().get_checks()

__all__ = ["PSD2Checker", "PSD2_CHECKS"]
