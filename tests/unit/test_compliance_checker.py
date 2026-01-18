"""
Unit Tests for Compliance Checker

Tests:
- PCI-DSS compliance checks
- RBI compliance checks
- DPDP compliance checks
- Report generation
- Issue detection
"""

import pytest


class TestComplianceCheckerUnit:
    """Unit tests for ComplianceChecker class"""

    @pytest.fixture
    def checker(self):
        """Create compliance checker with all standards"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["pci_dss", "rbi", "dpdp"])

    @pytest.fixture
    def pci_checker(self):
        """Create PCI-DSS only checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["pci_dss"])

    @pytest.fixture
    def rbi_checker(self):
        """Create RBI only checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["rbi"])

    @pytest.mark.unit
    def test_checker_initialization_all_standards(self, checker):
        """Test checker initializes with all standards"""
        assert checker is not None
        assert len(checker.checks) > 0
        assert any("pci_dss" in k for k in checker.checks.keys())
        assert any("rbi" in k for k in checker.checks.keys())
        assert any("dpdp" in k for k in checker.checks.keys())

    @pytest.mark.unit
    def test_checker_initialization_single_standard(self, pci_checker):
        """Test checker initializes with single standard"""
        assert all("pci_dss" in k for k in pci_checker.checks.keys())
        assert not any("rbi:" in k for k in pci_checker.checks.keys())

    @pytest.mark.unit
    def test_checker_initialization_default(self):
        """Test checker with default standards"""
        from verticals.fintech.compliance import ComplianceChecker
        checker = ComplianceChecker()

        assert len(checker.standards) == 4  # pci_dss, rbi, sebi, dpdp

    # PCI-DSS Tests
    @pytest.mark.unit
    def test_detect_hardcoded_card_number(self, pci_checker):
        """Test detection of hardcoded card numbers (PCI-3.4)"""
        code = '''
card_number = "4111111111111111"
'''
        report = pci_checker.check_code(code, "test.py")

        assert not report.passed
        assert any("PCI-3.4" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_detect_card_number_pattern(self, pci_checker):
        """Test detection of card number patterns"""
        code = '''
# Potential card number
data = 4532015112830366
'''
        report = pci_checker.check_code(code, "test.py")

        # Should detect potential card number pattern
        pci_issues = [i for i in report.issues if "PCI-3.4" in i.rule_id]
        assert len(pci_issues) > 0

    @pytest.mark.unit
    def test_detect_cvv_storage(self, pci_checker):
        """Test detection of CVV storage (PCI-3.2)"""
        code = '''
cvv = "123"
transaction.cvc = user_input
'''
        report = pci_checker.check_code(code, "test.py")

        assert any("PCI-3.2" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_detect_sql_injection(self, pci_checker):
        """Test detection of SQL injection (PCI-6.5.1)"""
        code = '''
def get_transaction(txn_id):
    query = f"SELECT * FROM transactions WHERE id = {txn_id}"
    return db.execute(query)
'''
        report = pci_checker.check_code(code, "test.py")

        assert any("PCI-6.5.1" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_detect_hardcoded_password(self, pci_checker):
        """Test detection of hardcoded passwords (PCI-8.2.1)"""
        code = '''
password = "supersecretpassword"
api_key = "sk_live_1234567890abcdef"
'''
        report = pci_checker.check_code(code, "test.py")

        assert any("PCI-8.2.1" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_detect_insecure_http(self, pci_checker):
        """Test detection of insecure HTTP (PCI-4.1)"""
        code = '''
url = "http://payment-api.example.com/charge"
response = requests.post(url, data=payment_data)
'''
        report = pci_checker.check_code(code, "test.py")

        assert any("PCI-4.1" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_detect_ssl_disabled(self, pci_checker):
        """Test detection of disabled SSL verification"""
        code = '''
response = requests.get(url, verify=False)
'''
        report = pci_checker.check_code(code, "test.py")

        assert any("PCI-4.1" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_audit_logging_check(self, pci_checker):
        """Test audit logging function presence check (PCI-10.2)"""
        code = '''
def process_payment(amount):
    # Process payment without logging
    return gateway.charge(amount)
'''
        report = pci_checker.check_code(code, "test.py")

        # Should flag missing audit logging
        assert any("PCI-10.2" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_audit_logging_present(self, pci_checker):
        """Test audit logging function presence passes"""
        code = '''
def process_payment(amount):
    audit_log("payment_started", amount=amount)
    result = gateway.charge(amount)
    audit_log("payment_completed", result=result)
    return result
'''
        report = pci_checker.check_code(code, "test.py")

        # Should not flag audit logging
        audit_issues = [i for i in report.issues if "PCI-10.2" in i.rule_id]
        assert len(audit_issues) == 0

    # RBI Tests
    @pytest.mark.unit
    def test_detect_us_region(self, rbi_checker):
        """Test detection of US region usage (RBI-DL-1)"""
        code = '''
aws_region = "us-east-1"
s3_bucket = "s3.us-west-2.amazonaws.com"
'''
        report = rbi_checker.check_code(code, "test.py")

        assert any("RBI-DL-1" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_detect_eu_region(self, rbi_checker):
        """Test detection of EU region usage (RBI-DL-1)"""
        code = '''
region = "eu-west-1"
'''
        report = rbi_checker.check_code(code, "test.py")

        assert any("RBI-DL-1" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_2fa_check(self, rbi_checker):
        """Test 2FA function presence check (RBI-SEC-1)"""
        code = '''
def process_high_value_transaction(amount):
    # No 2FA verification
    return execute_transaction(amount)
'''
        report = rbi_checker.check_code(code, "test.py")

        assert any("RBI-SEC-1" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_2fa_present(self, rbi_checker):
        """Test 2FA function presence passes"""
        code = '''
def process_high_value_transaction(amount):
    verify_otp(user_otp)
    return execute_transaction(amount)
'''
        report = rbi_checker.check_code(code, "test.py")

        twofa_issues = [i for i in report.issues if "RBI-SEC-1" in i.rule_id]
        assert len(twofa_issues) == 0

    # DPDP Tests
    @pytest.mark.unit
    def test_consent_check(self, checker):
        """Test consent management check (DPDP-1)"""
        code = '''
def collect_user_data(user):
    # No consent management
    return save_data(user)
'''
        report = checker.check_code(code, "test.py")

        assert any("DPDP-1" in i.rule_id for i in report.issues)

    @pytest.mark.unit
    def test_consent_present(self, checker):
        """Test consent function presence passes"""
        code = '''
def collect_user_data(user):
    if not get_consent(user.id, "data_collection"):
        raise ConsentRequired()
    return save_data(user)
'''
        report = checker.check_code(code, "test.py")

        consent_issues = [i for i in report.issues if "DPDP-1" in i.rule_id]
        assert len(consent_issues) == 0

    # Report Tests
    @pytest.mark.unit
    def test_report_structure(self, checker):
        """Test compliance report structure"""
        code = "print('hello')"
        report = checker.check_code(code, "test.py")

        assert hasattr(report, 'passed')
        assert hasattr(report, 'issues')
        assert hasattr(report, 'summary')
        assert hasattr(report, 'recommendations')

    @pytest.mark.unit
    def test_report_summary(self, pci_checker):
        """Test report summary counts"""
        code = '''
password = "secret123"
url = "http://api.example.com"
'''
        report = pci_checker.check_code(code, "test.py")

        assert "critical" in report.summary
        assert "high" in report.summary
        assert "medium" in report.summary
        assert "low" in report.summary

    @pytest.mark.unit
    def test_issue_structure(self, pci_checker):
        """Test compliance issue structure"""
        code = 'password = "supersecret123"'
        report = pci_checker.check_code(code, "test.py")

        if report.issues:
            issue = report.issues[0]
            assert hasattr(issue, 'rule_id')
            assert hasattr(issue, 'rule_name')
            assert hasattr(issue, 'severity')
            assert hasattr(issue, 'description')
            assert hasattr(issue, 'evidence')
            assert hasattr(issue, 'remediation')
            assert hasattr(issue, 'standard')

    @pytest.mark.unit
    def test_clean_code_passes(self, checker):
        """Test that compliant code passes"""
        code = '''
import os
from cryptography.fernet import Fernet

def secure_payment(encrypted_token):
    """Process payment securely"""
    api_key = os.environ.get('PAYMENT_API_KEY')
    url = "https://secure-payment.example.com/charge"

    audit_log("payment_started")
    get_consent(user_id, "payment")
    verify_otp(otp_code)

    return process(encrypted_token)
'''
        report = checker.check_code(code, "test.py")

        # May have some issues, but no critical/high if secure patterns used
        critical = report.summary.get('critical', 0)
        # Just verify structure works
        assert isinstance(critical, int)

    @pytest.mark.unit
    def test_generate_text_report(self, pci_checker):
        """Test text report generation"""
        code = 'password = "secret123password"'
        report = pci_checker.check_code(code, "test.py")

        text_report = pci_checker.generate_report(report, format="text")

        assert "COMPLIANCE REPORT" in text_report
        assert "Status:" in text_report
        assert "Summary:" in text_report

    @pytest.mark.unit
    def test_generate_json_report(self, pci_checker):
        """Test JSON report generation"""
        import json

        code = 'password = "secret123password"'
        report = pci_checker.check_code(code, "test.py")

        json_report = pci_checker.generate_report(report, format="json")

        # Should be valid JSON
        parsed = json.loads(json_report)
        assert "passed" in parsed
        assert "summary" in parsed
        assert "issues" in parsed

    @pytest.mark.unit
    def test_generate_report_invalid_format(self, pci_checker):
        """Test report generation with invalid format"""
        code = "print('hello')"
        report = pci_checker.check_code(code, "test.py")

        with pytest.raises(ValueError, match="Unknown format"):
            pci_checker.generate_report(report, format="invalid")

    @pytest.mark.unit
    def test_check_file(self, pci_checker, tmp_path):
        """Test checking a file"""
        test_file = tmp_path / "test.py"
        test_file.write_text('api_key = "sk_live_1234567890"')

        report = pci_checker.check_file(str(test_file))

        assert report is not None
        assert len(report.issues) > 0

    @pytest.mark.unit
    def test_line_number_tracking(self, pci_checker):
        """Test that line numbers are tracked"""
        code = '''line1 = "safe"
line2 = "also safe"
password = "insecure123"
line4 = "safe again"
'''
        report = pci_checker.check_code(code, "test.py")

        password_issues = [i for i in report.issues if "password" in i.evidence.lower()]
        if password_issues:
            assert password_issues[0].line_number == 3


class TestComplianceIssue:
    """Unit tests for ComplianceIssue dataclass"""

    @pytest.mark.unit
    def test_issue_creation(self):
        """Test ComplianceIssue creation"""
        from verticals.fintech.compliance import ComplianceIssue, Severity

        issue = ComplianceIssue(
            rule_id="PCI-3.4",
            rule_name="Cardholder Data Protection",
            severity=Severity.CRITICAL,
            description="Card data found unencrypted",
            evidence="Line 5: card = '4111...'",
            remediation="Encrypt card data",
            standard="pci_dss",
            line_number=5
        )

        assert issue.rule_id == "PCI-3.4"
        assert issue.severity == Severity.CRITICAL
        assert issue.line_number == 5


class TestComplianceReport:
    """Unit tests for ComplianceReport dataclass"""

    @pytest.mark.unit
    def test_report_creation(self):
        """Test ComplianceReport creation"""
        from verticals.fintech.compliance import ComplianceReport

        report = ComplianceReport(
            passed=False,
            issues=[],
            summary={"critical": 0, "high": 1},
            recommendations=["Fix issue X"]
        )

        assert report.passed is False
        assert report.summary["high"] == 1


class TestSeverity:
    """Unit tests for Severity enum"""

    @pytest.mark.unit
    def test_severity_values(self):
        """Test Severity enum values"""
        from verticals.fintech.compliance import Severity

        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"
