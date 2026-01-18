"""
PSR Compliance Checker

Payment Systems Regulator requirements covering:
- APP Fraud Reimbursement
- Access to Payment Systems
- Confirmation of Payee
- Faster Payments Requirements
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("psr")
class PSRChecker(BaseComplianceChecker):
    """PSR compliance checker for UK payment systems"""

    def __init__(self):
        super().__init__()
        self.standard_name = "psr"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all PSR compliance checks"""
        return {
            "PSR-APP-1": ComplianceCheck(
                check_id="PSR-APP-1",
                name="APP Fraud Reimbursement",
                description="Reimburse victims of APP fraud within required timeframe",
                severity=Severity.CRITICAL,
                remediation="Implement APP fraud detection and mandatory reimbursement (split 50/50 sending/receiving PSP).",
                standard="psr",
                article="APP Fraud Policy Statement",
                check_type="function_presence",
                required_functions=["detect_app_fraud", "reimburse_fraud_victim", "app_fraud_check"],
            ),
            "PSR-APP-2": ComplianceCheck(
                check_id="PSR-APP-2",
                name="APP Fraud Prevention",
                description="Implement effective fraud prevention measures",
                severity=Severity.HIGH,
                remediation="Implement behavioral analytics, warnings, and confirmation of payee.",
                standard="psr",
                article="APP Fraud Contingent Reimbursement",
                check_type="function_presence",
                required_functions=["fraud_warning", "verify_payee", "transaction_monitoring"],
            ),
            "PSR-COP-1": ComplianceCheck(
                check_id="PSR-COP-1",
                name="Confirmation of Payee",
                description="Verify payee name before payment",
                severity=Severity.HIGH,
                remediation="Implement CoP checking against payee account name.",
                standard="psr",
                article="Specific Direction 10",
                check_type="function_presence",
                required_functions=["confirm_payee", "verify_account_name", "cop_check"],
            ),
            "PSR-COP-2": ComplianceCheck(
                check_id="PSR-COP-2",
                name="CoP Response Handling",
                description="Handle CoP match, partial match, and no match appropriately",
                severity=Severity.HIGH,
                remediation="Display appropriate warnings for partial/no match. Allow user override with confirmation.",
                standard="psr",
                article="Specific Direction 10",
                check_type="function_presence",
                required_functions=["handle_cop_result", "show_cop_warning", "cop_override"],
            ),
            "PSR-ACCESS-1": ComplianceCheck(
                check_id="PSR-ACCESS-1",
                name="Access to Payment Systems",
                description="Fair access to payment systems",
                severity=Severity.MEDIUM,
                remediation="Ensure non-discriminatory access to Faster Payments, BACS, CHAPS.",
                standard="psr",
                article="FSBRA 2013",
                check_type="documentation",
            ),
            "PSR-FPS-1": ComplianceCheck(
                check_id="PSR-FPS-1",
                name="Faster Payments Limits",
                description="Adhere to Faster Payments transaction limits",
                severity=Severity.HIGH,
                remediation="Implement FPS limit of £1 million per transaction (participant dependent).",
                standard="psr",
                article="FPS Scheme Rules",
                patterns=[
                    r"amount\s*>\s*1000000",  # Over £1M
                ],
            ),
            "PSR-FPS-2": ComplianceCheck(
                check_id="PSR-FPS-2",
                name="Faster Payments Availability",
                description="Maintain required service availability",
                severity=Severity.HIGH,
                remediation="Maintain 99.7% availability for Faster Payments.",
                standard="psr",
                article="FPS Scheme Rules",
                check_type="function_presence",
                required_functions=["health_check", "monitor_availability", "service_status"],
            ),
            "PSR-BACS-1": ComplianceCheck(
                check_id="PSR-BACS-1",
                name="BACS Processing",
                description="Process BACS according to scheme rules",
                severity=Severity.MEDIUM,
                remediation="Implement 3-day BACS cycle. Handle returns appropriately.",
                standard="psr",
                article="BACS Scheme Rules",
                check_type="function_presence",
                required_functions=["submit_bacs", "process_bacs_return", "bacs_file"],
            ),
            "PSR-CHAPS-1": ComplianceCheck(
                check_id="PSR-CHAPS-1",
                name="CHAPS Processing",
                description="Process CHAPS for high-value payments",
                severity=Severity.MEDIUM,
                remediation="Implement CHAPS for same-day high-value (typically >£250k).",
                standard="psr",
                article="CHAPS Rules",
                check_type="function_presence",
                required_functions=["submit_chaps", "chaps_payment", "high_value_transfer"],
            ),
            "PSR-REPORT-1": ComplianceCheck(
                check_id="PSR-REPORT-1",
                name="PSR Reporting",
                description="Submit required reports to PSR",
                severity=Severity.MEDIUM,
                remediation="Submit fraud data, service metrics, and compliance reports.",
                standard="psr",
                article="PSR Reporting Requirements",
                check_type="function_presence",
                required_functions=["generate_psr_report", "submit_fraud_data", "service_metrics"],
            ),
        }


# Export for convenience
PSR_CHECKS = PSRChecker().get_checks()

__all__ = ["PSRChecker", "PSR_CHECKS"]
