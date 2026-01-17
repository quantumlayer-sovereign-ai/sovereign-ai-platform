"""
FinTech Compliance Checker

Automated compliance verification for:
- PCI-DSS
- RBI Guidelines
- SEBI Regulations
- DPDP Act
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import structlog

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
    standard: str  # pci_dss, rbi, sebi, dpdp
    line_number: Optional[int] = None


@dataclass
class ComplianceReport:
    """Compliance check report"""
    passed: bool
    issues: List[ComplianceIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


# PCI-DSS Compliance Checks
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


# RBI Compliance Checks
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


# DPDP Act Checks
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


class ComplianceChecker:
    """
    Automated compliance checker for FinTech code
    """

    def __init__(self, standards: Optional[List[str]] = None):
        """
        Initialize compliance checker

        Args:
            standards: List of standards to check (pci_dss, rbi, dpdp)
                      If None, checks all standards
        """
        self.standards = standards or ["pci_dss", "rbi", "dpdp"]
        self.checks = {}

        if "pci_dss" in self.standards:
            self.checks.update({f"pci_dss:{k}": v for k, v in PCI_DSS_CHECKS.items()})
        if "rbi" in self.standards:
            self.checks.update({f"rbi:{k}": v for k, v in RBI_CHECKS.items()})
        if "dpdp" in self.standards:
            self.checks.update({f"dpdp:{k}": v for k, v in DPDP_CHECKS.items()})

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
        recommendations = list(set(i.remediation for i in issues))

        passed = summary["critical"] == 0 and summary["high"] == 0

        logger.info("compliance_check_complete",
                   filename=filename,
                   passed=passed,
                   critical=summary["critical"],
                   high=summary["high"])

        return ComplianceReport(
            passed=passed,
            issues=issues,
            summary=summary,
            recommendations=recommendations
        )

    def check_file(self, filepath: str) -> ComplianceReport:
        """Check a file for compliance issues"""
        with open(filepath, 'r') as f:
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
