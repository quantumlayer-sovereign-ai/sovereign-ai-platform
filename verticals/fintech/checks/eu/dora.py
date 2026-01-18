"""
DORA Compliance Checker

Digital Operational Resilience Act (EU) 2022/2554 covering:
- ICT Risk Management
- ICT Incident Management
- Digital Operational Resilience Testing
- Third-Party Risk Management
- Information Sharing
"""

from ..base import (
    BaseComplianceChecker,
    ComplianceCheck,
    Severity,
    register_checker,
)


@register_checker("dora")
class DORAChecker(BaseComplianceChecker):
    """DORA compliance checker for digital operational resilience"""

    def __init__(self):
        super().__init__()
        self.standard_name = "dora"

    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all DORA compliance checks"""
        return {
            "DORA-ICT-1": ComplianceCheck(
                check_id="DORA-ICT-1",
                name="ICT Risk Management Framework",
                description="Implement comprehensive ICT risk management framework",
                severity=Severity.HIGH,
                remediation="Establish ICT risk management with policies, procedures, and governance.",
                standard="dora",
                article="Article 5-16",
                check_type="documentation",
            ),
            "DORA-ICT-2": ComplianceCheck(
                check_id="DORA-ICT-2",
                name="Asset Management",
                description="Maintain inventory of ICT assets and dependencies",
                severity=Severity.HIGH,
                remediation="Implement asset inventory with classification and dependency mapping.",
                standard="dora",
                article="Article 8",
                check_type="function_presence",
                required_functions=["get_asset_inventory", "track_dependencies", "asset_classification"],
            ),
            "DORA-ICT-3": ComplianceCheck(
                check_id="DORA-ICT-3",
                name="Access Control",
                description="Implement strict access control policies",
                severity=Severity.HIGH,
                remediation="Implement least privilege, MFA, and access logging.",
                standard="dora",
                article="Article 9",
                check_type="function_presence",
                required_functions=["check_access", "verify_mfa", "audit_access"],
            ),
            "DORA-INC-1": ComplianceCheck(
                check_id="DORA-INC-1",
                name="Incident Detection",
                description="Implement mechanisms for detecting ICT-related incidents",
                severity=Severity.CRITICAL,
                remediation="Implement monitoring, alerting, and anomaly detection.",
                standard="dora",
                article="Article 17",
                check_type="function_presence",
                required_functions=["detect_incident", "alert_on_anomaly", "monitor_systems"],
            ),
            "DORA-INC-2": ComplianceCheck(
                check_id="DORA-INC-2",
                name="Incident Classification",
                description="Classify incidents based on severity and impact",
                severity=Severity.HIGH,
                remediation="Implement incident classification with major incident criteria.",
                standard="dora",
                article="Article 18",
                check_type="function_presence",
                required_functions=["classify_incident", "assess_impact", "determine_severity"],
            ),
            "DORA-INC-3": ComplianceCheck(
                check_id="DORA-INC-3",
                name="Incident Reporting",
                description="Report major incidents to competent authorities",
                severity=Severity.CRITICAL,
                remediation="Implement incident reporting within required timeframes.",
                standard="dora",
                article="Article 19",
                check_type="function_presence",
                required_functions=["report_incident", "notify_authority", "incident_communication"],
            ),
            "DORA-TEST-1": ComplianceCheck(
                check_id="DORA-TEST-1",
                name="Resilience Testing Program",
                description="Conduct regular digital operational resilience testing",
                severity=Severity.HIGH,
                remediation="Implement testing program: vulnerability scans, TLPT, scenario testing.",
                standard="dora",
                article="Article 24-27",
                check_type="documentation",
            ),
            "DORA-TEST-2": ComplianceCheck(
                check_id="DORA-TEST-2",
                name="Threat-Led Penetration Testing",
                description="Conduct TLPT for critical functions at least every 3 years",
                severity=Severity.MEDIUM,
                remediation="Engage qualified testers for TLPT on critical systems.",
                standard="dora",
                article="Article 26",
                check_type="documentation",
            ),
            "DORA-TPP-1": ComplianceCheck(
                check_id="DORA-TPP-1",
                name="Third-Party ICT Risk",
                description="Manage ICT third-party provider risk",
                severity=Severity.HIGH,
                remediation="Implement third-party risk assessment, monitoring, and exit strategies.",
                standard="dora",
                article="Article 28-44",
                check_type="function_presence",
                required_functions=["assess_vendor_risk", "monitor_tpp", "vendor_due_diligence"],
            ),
            "DORA-TPP-2": ComplianceCheck(
                check_id="DORA-TPP-2",
                name="Critical TPP Concentration",
                description="Avoid excessive concentration risk with critical TPPs",
                severity=Severity.HIGH,
                remediation="Implement multi-vendor strategy and exit plans for critical services.",
                standard="dora",
                article="Article 29",
                check_type="documentation",
            ),
            "DORA-BCP-1": ComplianceCheck(
                check_id="DORA-BCP-1",
                name="Business Continuity",
                description="Maintain ICT business continuity policy",
                severity=Severity.CRITICAL,
                remediation="Implement BCP with RTO/RPO, backup, and disaster recovery.",
                standard="dora",
                article="Article 11",
                check_type="function_presence",
                required_functions=["backup_data", "disaster_recovery", "failover"],
            ),
            "DORA-BCP-2": ComplianceCheck(
                check_id="DORA-BCP-2",
                name="Recovery Testing",
                description="Regular testing of recovery procedures",
                severity=Severity.HIGH,
                remediation="Test backup restoration and failover procedures annually.",
                standard="dora",
                article="Article 11",
                check_type="documentation",
            ),
        }


# Export for convenience
DORA_CHECKS = DORAChecker().get_checks()

__all__ = ["DORAChecker", "DORA_CHECKS"]
