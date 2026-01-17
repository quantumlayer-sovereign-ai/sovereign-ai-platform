"""
Security Scanning Tools

Code security analysis and vulnerability detection
"""

import re
import ast
from typing import Dict, Any, List, Optional
from pathlib import Path
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
class SecurityIssue:
    rule_id: str
    rule_name: str
    severity: Severity
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


class SecurityScanner:
    """
    Security vulnerability scanner for code

    Features:
    - OWASP Top 10 detection
    - SQL Injection patterns
    - XSS vulnerabilities
    - Hardcoded secrets
    - Insecure configurations
    - Crypto weaknesses
    """

    # Security rules
    RULES = {
        # SQL Injection
        "SEC001": {
            "name": "SQL Injection",
            "severity": Severity.CRITICAL,
            "patterns": [
                r'execute\s*\(\s*["\'].*%[sd]',
                r'execute\s*\(\s*f["\']',
                r'execute\s*\(\s*["\'].*\+',
                r'cursor\.execute\s*\([^,]+\+',
                r'\.format\s*\([^)]*\)\s*\)',
            ],
            "description": "SQL query built with string concatenation or formatting",
            "recommendation": "Use parameterized queries with placeholders",
            "cwe_id": "CWE-89",
            "owasp_category": "A03:2021-Injection"
        },

        # XSS
        "SEC002": {
            "name": "Cross-Site Scripting (XSS)",
            "severity": Severity.HIGH,
            "patterns": [
                r'innerHTML\s*=',
                r'document\.write\s*\(',
                r'\.html\s*\([^)]*\+',
                r'dangerouslySetInnerHTML',
                r'v-html\s*=',
            ],
            "description": "Potential XSS vulnerability through unescaped output",
            "recommendation": "Escape all user-controlled data before rendering",
            "cwe_id": "CWE-79",
            "owasp_category": "A03:2021-Injection"
        },

        # Hardcoded Secrets
        "SEC003": {
            "name": "Hardcoded Secret",
            "severity": Severity.CRITICAL,
            "patterns": [
                r'password\s*=\s*["\'][^"\']{8,}["\']',
                r'api_key\s*=\s*["\'][^"\']{16,}["\']',
                r'secret\s*=\s*["\'][^"\']{8,}["\']',
                r'token\s*=\s*["\'][^"\']{20,}["\']',
                r'aws_secret_access_key\s*=\s*["\']',
                r'private_key\s*=\s*["\']',
            ],
            "description": "Hardcoded secret or credential detected",
            "recommendation": "Use environment variables or secret management",
            "cwe_id": "CWE-798",
            "owasp_category": "A02:2021-Cryptographic Failures"
        },

        # Insecure HTTP
        "SEC004": {
            "name": "Insecure HTTP",
            "severity": Severity.MEDIUM,
            "patterns": [
                r'http://(?!localhost|127\.0\.0\.1)',
                r'requests\.get\s*\(["\']http://',
                r'urllib\.request\.urlopen\s*\(["\']http://',
            ],
            "description": "HTTP used instead of HTTPS for non-local URL",
            "recommendation": "Use HTTPS for all external communications",
            "cwe_id": "CWE-319",
            "owasp_category": "A02:2021-Cryptographic Failures"
        },

        # Weak Cryptography
        "SEC005": {
            "name": "Weak Cryptographic Algorithm",
            "severity": Severity.HIGH,
            "patterns": [
                r'md5\s*\(',
                r'sha1\s*\(',
                r'DES\.',
                r'RC4',
                r'\.new\s*\(\s*["\']DES',
            ],
            "description": "Weak or deprecated cryptographic algorithm detected",
            "recommendation": "Use SHA-256 or stronger for hashing, AES-256 for encryption",
            "cwe_id": "CWE-327",
            "owasp_category": "A02:2021-Cryptographic Failures"
        },

        # Command Injection
        "SEC006": {
            "name": "Command Injection",
            "severity": Severity.CRITICAL,
            "patterns": [
                r'os\.system\s*\([^)]*\+',
                r'subprocess\.call\s*\(\s*["\'][^"\']*\+',
                r'subprocess\.run\s*\(\s*["\'][^"\']*\+',
                r'shell=True',
                r'exec\s*\([^)]*\+',
            ],
            "description": "Potential command injection vulnerability",
            "recommendation": "Use subprocess with list arguments, avoid shell=True",
            "cwe_id": "CWE-78",
            "owasp_category": "A03:2021-Injection"
        },

        # Path Traversal
        "SEC007": {
            "name": "Path Traversal",
            "severity": Severity.HIGH,
            "patterns": [
                r'open\s*\([^)]*\+[^)]*\)',
                r'Path\s*\([^)]*\+',
                r'\.\./',
            ],
            "description": "Potential path traversal vulnerability",
            "recommendation": "Validate and sanitize file paths, use absolute paths",
            "cwe_id": "CWE-22",
            "owasp_category": "A01:2021-Broken Access Control"
        },

        # SSRF
        "SEC008": {
            "name": "Server-Side Request Forgery",
            "severity": Severity.HIGH,
            "patterns": [
                r'requests\.(get|post|put)\s*\([^)]*\+',
                r'urllib\.request\.urlopen\s*\([^)]*\+',
            ],
            "description": "Potential SSRF vulnerability with user-controlled URL",
            "recommendation": "Validate and whitelist allowed URLs",
            "cwe_id": "CWE-918",
            "owasp_category": "A10:2021-SSRF"
        },

        # Insecure Deserialization
        "SEC009": {
            "name": "Insecure Deserialization",
            "severity": Severity.CRITICAL,
            "patterns": [
                r'pickle\.loads?\s*\(',
                r'yaml\.load\s*\([^)]*\)(?!\s*,\s*Loader)',
                r'yaml\.unsafe_load',
                r'marshal\.loads',
            ],
            "description": "Insecure deserialization detected",
            "recommendation": "Use safe deserialization methods, validate input",
            "cwe_id": "CWE-502",
            "owasp_category": "A08:2021-Software and Data Integrity Failures"
        },

        # Debug Mode
        "SEC010": {
            "name": "Debug Mode Enabled",
            "severity": Severity.MEDIUM,
            "patterns": [
                r'DEBUG\s*=\s*True',
                r'debug\s*=\s*True',
                r'app\.run\s*\([^)]*debug\s*=\s*True',
            ],
            "description": "Debug mode enabled in production code",
            "recommendation": "Disable debug mode in production",
            "cwe_id": "CWE-489",
            "owasp_category": "A05:2021-Security Misconfiguration"
        },

        # Missing CSRF Protection
        "SEC011": {
            "name": "Missing CSRF Protection",
            "severity": Severity.MEDIUM,
            "patterns": [
                r'@csrf_exempt',
                r'csrf_protect\s*=\s*False',
            ],
            "description": "CSRF protection disabled",
            "recommendation": "Enable CSRF protection for state-changing endpoints",
            "cwe_id": "CWE-352",
            "owasp_category": "A01:2021-Broken Access Control"
        },

        # Sensitive Data Exposure
        "SEC012": {
            "name": "Sensitive Data in Logs",
            "severity": Severity.HIGH,
            "patterns": [
                r'logger?\.(info|debug|warning|error)\s*\([^)]*password',
                r'print\s*\([^)]*password',
                r'logger?\.(info|debug|warning|error)\s*\([^)]*card',
                r'logger?\.(info|debug|warning|error)\s*\([^)]*token',
            ],
            "description": "Potentially logging sensitive data",
            "recommendation": "Never log passwords, tokens, or PII",
            "cwe_id": "CWE-532",
            "owasp_category": "A09:2021-Security Logging and Monitoring Failures"
        },

        # Insufficient Input Validation
        "SEC013": {
            "name": "Missing Input Validation",
            "severity": Severity.MEDIUM,
            "patterns": [
                r'request\.(args|form|json)\.get\s*\([^)]+\)[^.]*[+\-*/]',
                r'int\s*\(\s*request\.',
            ],
            "description": "User input used without validation",
            "recommendation": "Validate and sanitize all user inputs",
            "cwe_id": "CWE-20",
            "owasp_category": "A03:2021-Injection"
        },
    }

    def __init__(self):
        self.issues: List[SecurityIssue] = []

    def scan_code(self, code: str, file_path: str = "code.py") -> Dict[str, Any]:
        """
        Scan code for security vulnerabilities

        Args:
            code: Source code to scan
            file_path: File path for reporting

        Returns:
            Dict with scan results
        """
        self.issues = []
        lines = code.split('\n')

        for rule_id, rule in self.RULES.items():
            for pattern in rule['patterns']:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip if in comment
                        stripped = line.lstrip()
                        if stripped.startswith('#') or stripped.startswith('//'):
                            continue

                        self.issues.append(SecurityIssue(
                            rule_id=rule_id,
                            rule_name=rule['name'],
                            severity=rule['severity'],
                            description=rule['description'],
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=line.strip()[:100],
                            recommendation=rule['recommendation'],
                            cwe_id=rule.get('cwe_id'),
                            owasp_category=rule.get('owasp_category')
                        ))

        return self._generate_report()

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a file for security vulnerabilities"""
        path = Path(file_path)

        if not path.exists():
            return {'success': False, 'error': f'File not found: {file_path}'}

        try:
            code = path.read_text()
            return self.scan_code(code, str(path))
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def scan_directory(self, directory: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Scan all files in a directory"""
        extensions = extensions or ['.py', '.js', '.java', '.go', '.ts']
        dir_path = Path(directory)

        if not dir_path.exists():
            return {'success': False, 'error': f'Directory not found: {directory}'}

        all_issues = []

        for ext in extensions:
            for file_path in dir_path.rglob(f'*{ext}'):
                try:
                    code = file_path.read_text()
                    self.issues = []
                    self.scan_code(code, str(file_path))
                    all_issues.extend(self.issues)
                except Exception as e:
                    logger.warning("scan_file_failed", file=str(file_path), error=str(e))

        self.issues = all_issues
        return self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """Generate security scan report"""
        severity_counts = {s.value: 0 for s in Severity}
        for issue in self.issues:
            severity_counts[issue.severity.value] += 1

        return {
            'success': True,
            'total_issues': len(self.issues),
            'severity_counts': severity_counts,
            'passed': severity_counts['critical'] == 0 and severity_counts['high'] == 0,
            'issues': [
                {
                    'rule_id': i.rule_id,
                    'rule_name': i.rule_name,
                    'severity': i.severity.value,
                    'description': i.description,
                    'file': i.file_path,
                    'line': i.line_number,
                    'code': i.code_snippet,
                    'recommendation': i.recommendation,
                    'cwe': i.cwe_id,
                    'owasp': i.owasp_category
                }
                for i in sorted(self.issues, key=lambda x: list(Severity).index(x.severity))
            ]
        }

    def get_summary(self) -> str:
        """Get human-readable summary"""
        if not self.issues:
            return "No security issues found."

        critical = sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
        high = sum(1 for i in self.issues if i.severity == Severity.HIGH)
        medium = sum(1 for i in self.issues if i.severity == Severity.MEDIUM)
        low = sum(1 for i in self.issues if i.severity == Severity.LOW)

        return (
            f"Security Scan Results:\n"
            f"  Critical: {critical}\n"
            f"  High: {high}\n"
            f"  Medium: {medium}\n"
            f"  Low: {low}\n"
            f"  Total: {len(self.issues)}"
        )


class DependencyScanner:
    """
    Scan dependencies for known vulnerabilities

    Checks against vulnerability databases
    """

    def __init__(self):
        self.vulnerabilities = []

    def scan_requirements(self, requirements_file: str) -> Dict[str, Any]:
        """Scan Python requirements.txt for vulnerabilities"""
        path = Path(requirements_file)

        if not path.exists():
            return {'success': False, 'error': f'File not found: {requirements_file}'}

        try:
            deps = []
            for line in path.read_text().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package==version or package>=version
                    parts = re.split(r'[=<>!~]', line)
                    if parts:
                        deps.append({
                            'package': parts[0],
                            'constraint': line,
                            'version': parts[-1] if len(parts) > 1 else 'any'
                        })

            # Check for known vulnerable packages (simplified)
            vulnerabilities = self._check_vulnerabilities(deps)

            return {
                'success': True,
                'dependencies': len(deps),
                'vulnerabilities': vulnerabilities,
                'has_vulnerabilities': len(vulnerabilities) > 0
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_vulnerabilities(self, deps: List[Dict]) -> List[Dict]:
        """Check dependencies against known vulnerabilities"""
        # Simplified check - in production would use OSV, NVD, or similar
        known_vulnerable = {
            'pyyaml': {
                'versions': ['<5.4'],
                'cve': 'CVE-2020-14343',
                'severity': 'critical'
            },
            'django': {
                'versions': ['<3.2.14'],
                'cve': 'CVE-2022-34265',
                'severity': 'high'
            },
            'pillow': {
                'versions': ['<9.0.1'],
                'cve': 'CVE-2022-22817',
                'severity': 'high'
            }
        }

        vulnerabilities = []

        for dep in deps:
            pkg = dep['package'].lower()
            if pkg in known_vulnerable:
                vulnerabilities.append({
                    'package': dep['package'],
                    'current_version': dep['version'],
                    'vulnerable_versions': known_vulnerable[pkg]['versions'],
                    'cve': known_vulnerable[pkg]['cve'],
                    'severity': known_vulnerable[pkg]['severity']
                })

        return vulnerabilities
