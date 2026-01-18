"""
Base Compliance Check Module

Provides abstract interface and common utilities for compliance checking.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    """Severity levels for compliance issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ComplianceCheck:
    """Definition of a single compliance check"""
    check_id: str
    name: str
    description: str
    severity: Severity
    remediation: str
    standard: str
    patterns: list[str] | None = None
    check_type: str = "pattern"  # pattern, function_presence, documentation
    required_functions: list[str] | None = None
    article: str | None = None  # For GDPR articles, FCA rules, etc.


@dataclass
class ComplianceIssue:
    """A compliance issue found during checking"""
    rule_id: str
    rule_name: str
    severity: Severity
    description: str
    evidence: str
    remediation: str
    standard: str
    line_number: int | None = None
    article: str | None = None


@dataclass
class ComplianceReport:
    """Compliance check report"""
    passed: bool
    issues: list[ComplianceIssue] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    standards_checked: list[str] = field(default_factory=list)


class BaseComplianceChecker(ABC):
    """
    Abstract base class for compliance checkers

    Each region/standard should implement this interface
    """

    def __init__(self):
        self.standard_name: str = ""
        self.checks: dict[str, ComplianceCheck] = {}

    @abstractmethod
    def get_checks(self) -> dict[str, ComplianceCheck]:
        """Return all compliance checks for this standard"""
        pass

    def check_code(self, code: str, filename: str = "code") -> list[ComplianceIssue]:
        """
        Check code for compliance issues

        Args:
            code: Source code to check
            filename: Name of the file being checked

        Returns:
            List of ComplianceIssue objects
        """
        issues = []
        checks = self.get_checks()

        for check_id, check in checks.items():
            # Pattern-based checks
            if check.check_type == "pattern" and check.patterns:
                for pattern in check.patterns:
                    for i, line in enumerate(code.split("\n"), 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(ComplianceIssue(
                                rule_id=check_id,
                                rule_name=check.name,
                                severity=check.severity,
                                description=check.description,
                                evidence=f"Line {i}: {line.strip()[:100]}",
                                remediation=check.remediation,
                                standard=self.standard_name,
                                line_number=i,
                                article=check.article
                            ))

            # Function presence checks
            elif check.check_type == "function_presence" and check.required_functions:
                found = any(
                    f"def {fn}" in code or f"{fn}(" in code
                    for fn in check.required_functions
                )
                if not found:
                    issues.append(ComplianceIssue(
                        rule_id=check_id,
                        rule_name=check.name,
                        severity=check.severity,
                        description=check.description,
                        evidence=f"Required functions not found: {check.required_functions}",
                        remediation=check.remediation,
                        standard=self.standard_name,
                        article=check.article
                    ))

        return issues

    @staticmethod
    def generate_summary(issues: list[ComplianceIssue]) -> dict[str, int]:
        """Generate summary of issue counts by severity"""
        return {
            "critical": sum(1 for i in issues if i.severity == Severity.CRITICAL),
            "high": sum(1 for i in issues if i.severity == Severity.HIGH),
            "medium": sum(1 for i in issues if i.severity == Severity.MEDIUM),
            "low": sum(1 for i in issues if i.severity == Severity.LOW),
            "info": sum(1 for i in issues if i.severity == Severity.INFO),
        }


class ComplianceCheckerRegistry:
    """Registry of all compliance checkers by region and standard"""

    _checkers: dict[str, type[BaseComplianceChecker]] = {}

    @classmethod
    def register(cls, standard: str, checker_class: type[BaseComplianceChecker]):
        """Register a compliance checker"""
        cls._checkers[standard] = checker_class

    @classmethod
    def get(cls, standard: str) -> BaseComplianceChecker | None:
        """Get a checker instance by standard name"""
        checker_class = cls._checkers.get(standard)
        if checker_class:
            return checker_class()
        return None

    @classmethod
    def get_all(cls) -> dict[str, type[BaseComplianceChecker]]:
        """Get all registered checkers"""
        return cls._checkers.copy()

    @classmethod
    def list_standards(cls) -> list[str]:
        """List all registered standards"""
        return list(cls._checkers.keys())


def register_checker(standard: str):
    """Decorator to register a compliance checker"""
    def decorator(cls: type[BaseComplianceChecker]):
        ComplianceCheckerRegistry.register(standard, cls)
        return cls
    return decorator


__all__ = [
    "Severity",
    "ComplianceCheck",
    "ComplianceIssue",
    "ComplianceReport",
    "BaseComplianceChecker",
    "ComplianceCheckerRegistry",
    "register_checker",
]
