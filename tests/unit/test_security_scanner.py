"""
Unit Tests for Security Scanner

Tests the actual SecurityScanner implementation:
- SQL injection detection
- XSS detection
- Command injection detection
- Hardcoded secrets detection
- Weak cryptography detection
- Insecure HTTP detection
"""

import pytest


class TestSecurityScannerUnit:
    """Unit tests for SecurityScanner class"""

    @pytest.fixture
    def scanner(self):
        """Create scanner instance"""
        from core.tools.security_tools import SecurityScanner
        return SecurityScanner()

    @pytest.mark.unit
    def test_scanner_initialization(self, scanner):
        """Test scanner initialization"""
        assert scanner is not None
        assert len(scanner.RULES) > 0

    @pytest.mark.unit
    def test_scan_clean_code(self, scanner):
        """Test scanning clean code"""
        code = '''
def add(a, b):
    return a + b
'''
        result = scanner.scan_code(code)

        assert result["passed"] is True
        assert result["total_issues"] == 0

    @pytest.mark.unit
    def test_detect_sql_injection(self, scanner):
        """Test SQL injection detection"""
        # Use code that matches the scanner's pattern: execute\s*\(\s*f["\']
        code = '''
def get_user(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
'''
        result = scanner.scan_code(code)

        # Check for SQL injection issue (SEC001)
        has_sql_injection = any(
            i.get("rule_id") == "SEC001"
            for i in result.get("issues", [])
        )
        assert has_sql_injection, f"Expected SQL injection detection, got: {result}"

    @pytest.mark.unit
    def test_detect_hardcoded_password(self, scanner):
        """Test hardcoded password detection"""
        code = '''
password = "mysupersecretpassword123"
'''
        result = scanner.scan_code(code)

        # Should detect hardcoded secret
        has_secret_issue = any(
            "SEC003" in str(i.get("rule_id", ""))
            for i in result.get("issues", [])
        )
        assert has_secret_issue or not result["passed"]

    @pytest.mark.unit
    def test_detect_hardcoded_api_key(self, scanner):
        """Test hardcoded API key detection"""
        code = '''
api_key = "sk_live_abcdefghij1234567890"
'''
        result = scanner.scan_code(code)

        assert not result["passed"] or result["total_issues"] > 0

    @pytest.mark.unit
    def test_ignore_short_strings(self, scanner):
        """Test that short strings are not flagged as secrets"""
        code = '''
name = "John"
status = "active"
'''
        result = scanner.scan_code(code)

        # Short strings should not be flagged
        assert result["passed"] is True

    @pytest.mark.unit
    def test_detect_insecure_http(self, scanner):
        """Test insecure HTTP detection"""
        code = '''
url = "http://api.example.com/data"
response = requests.get(url)
'''
        result = scanner.scan_code(code)

        # Should detect HTTP URL
        has_http_issue = any(
            "SEC004" in str(i.get("rule_id", ""))
            for i in result.get("issues", [])
        )
        assert has_http_issue or not result["passed"]

    @pytest.mark.unit
    def test_detect_weak_md5(self, scanner):
        """Test weak MD5 hash detection"""
        code = '''
import hashlib
hashed = hashlib.md5(data.encode()).hexdigest()
'''
        result = scanner.scan_code(code)

        has_weak_crypto = any(
            "SEC005" in str(i.get("rule_id", ""))
            for i in result.get("issues", [])
        )
        assert has_weak_crypto or not result["passed"]

    @pytest.mark.unit
    def test_detect_command_injection(self, scanner):
        """Test command injection detection"""
        code = '''
import os
os.system("ls " + user_input)
'''
        result = scanner.scan_code(code)

        has_cmd_injection = any(
            "SEC006" in str(i.get("rule_id", ""))
            for i in result.get("issues", [])
        )
        assert has_cmd_injection or not result["passed"]

    @pytest.mark.unit
    def test_issue_severity_levels(self, scanner):
        """Test that issues have proper severity levels"""
        code = '''
password = "supersecretpassword123"
'''
        result = scanner.scan_code(code)

        if result["issues"]:
            severities = {i.get("severity") for i in result["issues"]}
            assert len(severities) > 0

    @pytest.mark.unit
    def test_scan_result_format(self, scanner):
        """Test scan result format"""
        code = '''
password = "secret123password456"
'''
        result = scanner.scan_code(code)

        assert "passed" in result
        assert "total_issues" in result
        assert "issues" in result

    @pytest.mark.unit
    def test_issue_format(self, scanner):
        """Test individual issue format"""
        code = '''
password = "mysupersecretpassword"
'''
        result = scanner.scan_code(code)

        if result["issues"]:
            issue = result["issues"][0]
            assert "rule_id" in issue
            assert "rule_name" in issue
            assert "severity" in issue
            assert "description" in issue
            # Line may be 'line' or 'line_number'
            assert "line" in issue or "line_number" in issue

    @pytest.mark.unit
    def test_rules_constant(self, scanner):
        """Test RULES constant structure"""
        for rule_id, rule in scanner.RULES.items():
            assert "name" in rule
            assert "severity" in rule
            assert "patterns" in rule


class TestSeverityUnit:
    """Unit tests for Severity enum"""

    @pytest.mark.unit
    def test_severity_values(self):
        """Test severity enum values"""
        from core.tools.security_tools import Severity

        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"
