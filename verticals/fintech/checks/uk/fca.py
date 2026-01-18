"""
FCA Compliance Checker

Financial Conduct Authority Handbook covering:
- PRIN (Principles for Businesses)
- SYSC (Senior Management Arrangements)
- COND (Threshold Conditions)
- Consumer Duty
- COBS (Conduct of Business Sourcebook)
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("fca")
class FCAChecker(BaseComplianceChecker):
    """FCA compliance checker for UK financial services"""

    def __init__(self):
        super().__init__()
        self.standard_name = "fca"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all FCA compliance checks"""
        return {
            "FCA-PRIN-1": ComplianceCheck(
                check_id="FCA-PRIN-1",
                name="Integrity",
                description="Conduct business with integrity",
                severity=Severity.HIGH,
                remediation="Implement controls ensuring business integrity.",
                standard="fca",
                article="PRIN 2.1.1R - Principle 1",
                check_type="documentation",
            ),
            "FCA-PRIN-2": ComplianceCheck(
                check_id="FCA-PRIN-2",
                name="Skill, Care and Diligence",
                description="Conduct business with due skill, care and diligence",
                severity=Severity.HIGH,
                remediation="Ensure competent staff and appropriate procedures.",
                standard="fca",
                article="PRIN 2.1.1R - Principle 2",
                check_type="documentation",
            ),
            "FCA-PRIN-6": ComplianceCheck(
                check_id="FCA-PRIN-6",
                name="Treating Customers Fairly",
                description="Pay due regard to interests of customers",
                severity=Severity.CRITICAL,
                remediation="Implement TCF outcomes. Design products with customer outcomes in mind.",
                standard="fca",
                article="PRIN 2.1.1R - Principle 6",
                check_type="documentation",
            ),
            "FCA-COND-1": ComplianceCheck(
                check_id="FCA-COND-1",
                name="Consumer Duty - Good Outcomes",
                description="Act to deliver good outcomes for retail customers",
                severity=Severity.CRITICAL,
                remediation="Design products and services for good customer outcomes. Monitor outcomes.",
                standard="fca",
                article="Consumer Duty PRIN 2A",
                check_type="function_presence",
                required_functions=["assess_customer_outcome", "monitor_outcomes", "customer_impact"],
            ),
            "FCA-COND-2": ComplianceCheck(
                check_id="FCA-COND-2",
                name="Consumer Duty - Fair Value",
                description="Products and services must provide fair value",
                severity=Severity.HIGH,
                remediation="Conduct fair value assessments. Document pricing rationale.",
                standard="fca",
                article="Consumer Duty PRIN 2A.4",
                check_type="documentation",
            ),
            "FCA-COND-3": ComplianceCheck(
                check_id="FCA-COND-3",
                name="Consumer Duty - Consumer Understanding",
                description="Ensure communications enable understanding",
                severity=Severity.HIGH,
                remediation="Test communications with consumers. Use plain language.",
                standard="fca",
                article="Consumer Duty PRIN 2A.5",
                check_type="documentation",
            ),
            "FCA-SYSC-1": ComplianceCheck(
                check_id="FCA-SYSC-1",
                name="Systems and Controls",
                description="Maintain adequate systems and controls",
                severity=Severity.HIGH,
                remediation="Implement governance, risk management, and compliance monitoring.",
                standard="fca",
                article="SYSC 4.1.1R",
                check_type="function_presence",
                required_functions=["compliance_check", "risk_assessment", "control_testing"],
            ),
            "FCA-SYSC-2": ComplianceCheck(
                check_id="FCA-SYSC-2",
                name="Record Keeping",
                description="Maintain adequate records",
                severity=Severity.HIGH,
                remediation="Implement audit trails and record retention (minimum 5 years).",
                standard="fca",
                article="SYSC 9.1.1R",
                check_type="function_presence",
                required_functions=["audit_log", "record_transaction", "create_audit_trail"],
            ),
            "FCA-COBS-1": ComplianceCheck(
                check_id="FCA-COBS-1",
                name="Fair, Clear Communications",
                description="Communications must be fair, clear, and not misleading",
                severity=Severity.HIGH,
                remediation="Review all customer communications for clarity and accuracy.",
                standard="fca",
                article="COBS 4.2.1R",
                check_type="documentation",
            ),
            "FCA-COBS-2": ComplianceCheck(
                check_id="FCA-COBS-2",
                name="Appropriateness Assessment",
                description="Assess appropriateness of products for customers",
                severity=Severity.HIGH,
                remediation="Implement appropriateness checks before selling complex products.",
                standard="fca",
                article="COBS 10",
                check_type="function_presence",
                required_functions=["assess_appropriateness", "suitability_check", "customer_assessment"],
            ),
            "FCA-SUP-1": ComplianceCheck(
                check_id="FCA-SUP-1",
                name="Regulatory Reporting",
                description="Submit required regulatory returns",
                severity=Severity.HIGH,
                remediation="Implement automated regulatory reporting. Monitor submission deadlines.",
                standard="fca",
                article="SUP 16",
                check_type="function_presence",
                required_functions=["generate_reg_report", "submit_regulatory", "compliance_return"],
            ),
            "FCA-SMCR-1": ComplianceCheck(
                check_id="FCA-SMCR-1",
                name="Senior Manager Accountability",
                description="Senior managers accountable for their areas",
                severity=Severity.HIGH,
                remediation="Document responsibilities. Implement management information.",
                standard="fca",
                article="SMCR",
                check_type="documentation",
            ),
        }


# Export for convenience
FCA_CHECKS = FCAChecker().get_checks()

__all__ = ["FCAChecker", "FCA_CHECKS"]
