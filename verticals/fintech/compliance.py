"""
FinTech Compliance Checker

Automated compliance verification for multiple regions:

India:
- PCI-DSS
- RBI Guidelines
- SEBI Regulations
- DPDP Act

EU:
- PCI-DSS
- GDPR
- PSD2
- eIDAS
- DORA

UK:
- PCI-DSS
- UK GDPR
- FCA Handbook
- PSR Requirements
"""

import re
from dataclasses import dataclass, field
from enum import Enum

import structlog

from .region import FinTechRegion, get_region_config, DEFAULT_REGION

logger = structlog.get_logger()


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ComplianceIssue:
    """A compliance issue found during checking"""
    rule_id: str
    rule_name: str
    severity: Severity
    description: str
    evidence: str
    remediation: str
    standard: str  # pci_dss, rbi, sebi, dpdp, gdpr, psd2, fca, etc.
    line_number: int | None = None
    article: str | None = None  # For GDPR articles, FCA rules, etc.


@dataclass
class ComplianceReport:
    """Compliance check report"""
    passed: bool
    issues: list[ComplianceIssue] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    region: str | None = None
    standards_checked: list[str] = field(default_factory=list)


# PCI-DSS Compliance Checks (Global - applies to all regions)
PCI_DSS_CHECKS = {
    "PCI-3.4": {
        "name": "Cardholder Data Protection",
        "description": "Card numbers must be masked or encrypted",
        "patterns": [
            r'\b\d{13,19}\b',  # Potential card numbers
            r'card[_-]?number\s*=\s*["\'][^"\']+["\']',  # Hardcoded card numbers
        ],
        "severity": Severity.CRITICAL,
        "remediation": "Use tokenization or encryption for card data. Never store full card numbers."
    },
    "PCI-3.2": {
        "name": "No Storage of Sensitive Auth Data",
        "description": "CVV/CVC must never be stored",
        "patterns": [
            r'cvv\s*=',
            r'cvc\s*=',
            r'security[_-]?code\s*=',
            r'\.cvv\s*=',
        ],
        "severity": Severity.CRITICAL,
        "remediation": "Never store CVV/CVC. Use payment gateway tokenization."
    },
    "PCI-6.5.1": {
        "name": "SQL Injection Prevention",
        "description": "Use parameterized queries",
        "patterns": [
            r'execute\s*\([^)]*%s',
            r'f"[^"]*SELECT[^"]*{',
            r'f"[^"]*INSERT[^"]*{',
            r'f"[^"]*UPDATE[^"]*{',
            r'f"[^"]*DELETE[^"]*{',
            r'\+\s*["\'].*SELECT',
        ],
        "severity": Severity.HIGH,
        "remediation": "Use parameterized queries or ORM. Never concatenate user input into SQL."
    },
    "PCI-8.2.1": {
        "name": "Credential Storage",
        "description": "No hardcoded credentials",
        "patterns": [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
        ],
        "severity": Severity.HIGH,
        "remediation": "Use environment variables or secret management (Vault, AWS Secrets Manager)."
    },
    "PCI-4.1": {
        "name": "Encryption in Transit",
        "description": "Use TLS for data transmission",
        "patterns": [
            r'http://',  # Non-HTTPS URLs
            r'verify\s*=\s*False',  # Disabled SSL verification
            r'ssl\s*=\s*False',
        ],
        "severity": Severity.HIGH,
        "remediation": "Use HTTPS/TLS 1.2+ for all data transmission. Never disable SSL verification."
    },
    "PCI-10.2": {
        "name": "Audit Logging",
        "description": "Log all access to cardholder data",
        "check_type": "function_presence",
        "required_functions": ["audit_log", "log_transaction", "create_audit_trail"],
        "severity": Severity.MEDIUM,
        "remediation": "Implement comprehensive audit logging for all financial operations."
    }
}


# RBI Compliance Checks (India)
RBI_CHECKS = {
    "RBI-DL-1": {
        "name": "Data Localization",
        "description": "Payment data must be stored in India",
        "patterns": [
            r'region\s*=\s*["\']us-',  # US AWS regions
            r'region\s*=\s*["\']eu-',  # EU AWS regions
            r'\.s3\.amazonaws\.com',  # Check for explicit S3 URLs
        ],
        "severity": Severity.CRITICAL,
        "remediation": "Use Indian data centers (ap-south-1 for AWS, asia-south1 for GCP)."
    },
    "RBI-PA-1": {
        "name": "Settlement Timeline",
        "description": "T+1 settlement for payment aggregators",
        "check_type": "documentation",
        "severity": Severity.HIGH,
        "remediation": "Implement T+1 settlement cycle. Document settlement process."
    },
    "RBI-SEC-1": {
        "name": "Two-Factor Authentication",
        "description": "2FA required for high-value transactions",
        "check_type": "function_presence",
        "required_functions": ["verify_otp", "send_otp", "two_factor_auth"],
        "severity": Severity.HIGH,
        "remediation": "Implement 2FA for transactions above threshold."
    }
}


# DPDP Act Checks (India)
DPDP_CHECKS = {
    "DPDP-1": {
        "name": "Consent Management",
        "description": "Must obtain explicit consent for data processing",
        "check_type": "function_presence",
        "required_functions": ["get_consent", "record_consent", "consent_management"],
        "severity": Severity.HIGH,
        "remediation": "Implement consent management system with audit trail."
    },
    "DPDP-2": {
        "name": "Data Minimization",
        "description": "Collect only necessary data",
        "check_type": "documentation",
        "severity": Severity.MEDIUM,
        "remediation": "Review data collection. Remove unnecessary fields."
    }
}


# GDPR Checks (EU)
GDPR_CHECKS = {
    "GDPR-ART17": {
        "name": "Right to Erasure",
        "description": "Data subjects have right to erasure",
        "check_type": "function_presence",
        "required_functions": ["delete_personal_data", "erase_user", "right_to_erasure"],
        "severity": Severity.CRITICAL,
        "remediation": "Implement data deletion mechanism with verification."
    },
    "GDPR-ART33": {
        "name": "Breach Notification (72 hours)",
        "description": "Personal data breach must be notified within 72 hours",
        "check_type": "function_presence",
        "required_functions": ["notify_breach", "report_breach", "breach_notification"],
        "severity": Severity.CRITICAL,
        "remediation": "Implement breach detection and 72-hour notification to DPA."
    },
    "GDPR-ART20": {
        "name": "Data Portability",
        "description": "Data subjects have right to data portability",
        "check_type": "function_presence",
        "required_functions": ["export_user_data", "data_portability", "download_my_data"],
        "severity": Severity.HIGH,
        "remediation": "Implement data export in machine-readable format."
    }
}


# PSD2 Checks (EU)
PSD2_CHECKS = {
    "PSD2-SCA-1": {
        "name": "Strong Customer Authentication",
        "description": "SCA required: 2 of 3 factors",
        "check_type": "function_presence",
        "required_functions": ["verify_sca", "strong_customer_auth", "two_factor_auth"],
        "severity": Severity.CRITICAL,
        "remediation": "Implement SCA with at least 2 independent elements."
    },
    "PSD2-SCA-2": {
        "name": "Dynamic Linking",
        "description": "Authentication code must be linked to amount and payee",
        "patterns": [
            r"static_otp",
            r"reusable_token",
            r"fixed_auth_code",
        ],
        "severity": Severity.CRITICAL,
        "remediation": "Generate authentication code dynamically linked to amount and recipient."
    }
}


# FCA Checks (UK)
FCA_CHECKS = {
    "FCA-COND-1": {
        "name": "Consumer Duty",
        "description": "Act to deliver good outcomes for retail customers",
        "check_type": "function_presence",
        "required_functions": ["assess_customer_outcome", "monitor_outcomes"],
        "severity": Severity.CRITICAL,
        "remediation": "Design products and services for good customer outcomes."
    },
    "FCA-SYSC-1": {
        "name": "Systems and Controls",
        "description": "Maintain adequate systems and controls",
        "check_type": "function_presence",
        "required_functions": ["compliance_check", "risk_assessment", "control_testing"],
        "severity": Severity.HIGH,
        "remediation": "Implement governance, risk management, and compliance monitoring."
    }
}


# UK GDPR Checks
UK_GDPR_CHECKS = {
    "UKGDPR-ART33": {
        "name": "ICO Breach Notification",
        "description": "Notify ICO of personal data breach within 72 hours",
        "check_type": "function_presence",
        "required_functions": ["notify_ico", "report_breach", "breach_notification"],
        "severity": Severity.CRITICAL,
        "remediation": "Implement breach detection and notification to ICO."
    }
}


# Region to checks mapping
REGION_CHECKS = {
    FinTechRegion.INDIA: {
        "pci_dss": PCI_DSS_CHECKS,
        "rbi": RBI_CHECKS,
        "dpdp": DPDP_CHECKS,
    },
    FinTechRegion.EU: {
        "pci_dss": PCI_DSS_CHECKS,
        "gdpr": GDPR_CHECKS,
        "psd2": PSD2_CHECKS,
    },
    FinTechRegion.UK: {
        "pci_dss": PCI_DSS_CHECKS,
        "uk_gdpr": UK_GDPR_CHECKS,
        "fca": FCA_CHECKS,
    },
}


class ComplianceChecker:
    """
    Automated compliance checker for FinTech code

    Supports region-aware compliance checking for:
    - India: PCI-DSS, RBI, DPDP
    - EU: PCI-DSS, GDPR, PSD2
    - UK: PCI-DSS, UK GDPR, FCA
    """

    def __init__(
        self,
        standards: list[str] | None = None,
        region: str | FinTechRegion | None = None
    ):
        """
        Initialize compliance checker

        Args:
            standards: List of standards to check. If None, uses region defaults.
            region: Region for compliance (india, eu, uk). Defaults to india.
        """
        # Handle region
        if region is not None:
            if isinstance(region, str):
                region = FinTechRegion(region.lower())
            self.region = region
        else:
            self.region = DEFAULT_REGION

        # Determine standards to check
        if standards is not None:
            self.standards = standards
        else:
            # Use region defaults
            region_config = get_region_config(self.region)
            self.standards = region_config.compliance_standards

        self.checks = {}

        # Load checks based on standards
        if "pci_dss" in self.standards:
            self.checks.update({f"pci_dss:{k}": v for k, v in PCI_DSS_CHECKS.items()})
        if "rbi" in self.standards:
            self.checks.update({f"rbi:{k}": v for k, v in RBI_CHECKS.items()})
        if "dpdp" in self.standards:
            self.checks.update({f"dpdp:{k}": v for k, v in DPDP_CHECKS.items()})
        if "gdpr" in self.standards:
            self.checks.update({f"gdpr:{k}": v for k, v in GDPR_CHECKS.items()})
        if "psd2" in self.standards:
            self.checks.update({f"psd2:{k}": v for k, v in PSD2_CHECKS.items()})
        if "uk_gdpr" in self.standards:
            self.checks.update({f"uk_gdpr:{k}": v for k, v in UK_GDPR_CHECKS.items()})
        if "fca" in self.standards:
            self.checks.update({f"fca:{k}": v for k, v in FCA_CHECKS.items()})

    def check_code(self, code: str, filename: str = "code") -> ComplianceReport:
        """
        Check code for compliance issues

        Args:
            code: Source code to check
            filename: Name of the file being checked

        Returns:
            ComplianceReport with findings
        """
        issues = []

        for rule_id, check in self.checks.items():
            standard = rule_id.split(":")[0]

            # Pattern-based checks
            if "patterns" in check:
                for pattern in check["patterns"]:
                    for i, line in enumerate(code.split("\n"), 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(ComplianceIssue(
                                rule_id=rule_id,
                                rule_name=check["name"],
                                severity=check["severity"],
                                description=check["description"],
                                evidence=f"Line {i}: {line.strip()[:100]}",
                                remediation=check["remediation"],
                                standard=standard,
                                line_number=i
                            ))

            # Function presence checks
            if check.get("check_type") == "function_presence":
                required = check.get("required_functions", [])
                found = any(f"def {fn}" in code or f"{fn}(" in code for fn in required)
                if not found:
                    issues.append(ComplianceIssue(
                        rule_id=rule_id,
                        rule_name=check["name"],
                        severity=check["severity"],
                        description=check["description"],
                        evidence=f"Required functions not found: {required}",
                        remediation=check["remediation"],
                        standard=standard
                    ))

        # Generate summary
        summary = {
            "critical": sum(1 for i in issues if i.severity == Severity.CRITICAL),
            "high": sum(1 for i in issues if i.severity == Severity.HIGH),
            "medium": sum(1 for i in issues if i.severity == Severity.MEDIUM),
            "low": sum(1 for i in issues if i.severity == Severity.LOW),
        }

        # Generate recommendations
        recommendations = list({i.remediation for i in issues})

        passed = summary["critical"] == 0 and summary["high"] == 0

        logger.info("compliance_check_complete",
                   filename=filename,
                   passed=passed,
                   region=self.region.value,
                   critical=summary["critical"],
                   high=summary["high"])

        return ComplianceReport(
            passed=passed,
            issues=issues,
            summary=summary,
            recommendations=recommendations,
            region=self.region.value,
            standards_checked=self.standards
        )

    def check_file(self, filepath: str) -> ComplianceReport:
        """Check a file for compliance issues"""
        with open(filepath) as f:
            code = f.read()
        return self.check_code(code, filepath)

    def generate_report(self, report: ComplianceReport, format: str = "text") -> str:
        """Generate formatted compliance report"""
        if format == "text":
            return self._generate_text_report(report)
        elif format == "json":
            return self._generate_json_report(report)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _generate_text_report(self, report: ComplianceReport) -> str:
        """Generate text-format report"""
        lines = [
            "=" * 60,
            "COMPLIANCE REPORT",
            "=" * 60,
            "",
            f"Status: {'PASSED' if report.passed else 'FAILED'}",
            "",
            "Summary:",
            f"  Critical: {report.summary.get('critical', 0)}",
            f"  High: {report.summary.get('high', 0)}",
            f"  Medium: {report.summary.get('medium', 0)}",
            f"  Low: {report.summary.get('low', 0)}",
            "",
        ]

        if report.issues:
            lines.append("Issues Found:")
            lines.append("-" * 40)
            for issue in report.issues:
                lines.extend([
                    f"[{issue.severity.value.upper()}] {issue.rule_id}",
                    f"  {issue.rule_name}",
                    f"  Evidence: {issue.evidence}",
                    f"  Fix: {issue.remediation}",
                    ""
                ])

        if report.recommendations:
            lines.append("Recommendations:")
            lines.append("-" * 40)
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def _generate_json_report(self, report: ComplianceReport) -> str:
        """Generate JSON-format report"""
        import json
        return json.dumps({
            "passed": report.passed,
            "summary": report.summary,
            "issues": [
                {
                    "rule_id": i.rule_id,
                    "rule_name": i.rule_name,
                    "severity": i.severity.value,
                    "description": i.description,
                    "evidence": i.evidence,
                    "remediation": i.remediation,
                    "standard": i.standard,
                    "line_number": i.line_number
                }
                for i in report.issues
            ],
            "recommendations": report.recommendations
        }, indent=2)
