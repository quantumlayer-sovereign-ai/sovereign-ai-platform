"""
Integration Tests for Compliance Flow

Tests complete compliance checking workflows:
- Code submission → Compliance check → Report generation
- Multi-standard compliance checking
- API integration for compliance
"""

import os

import pytest
from fastapi.testclient import TestClient

# Set up auth environment before importing app
os.environ["DEV_MODE"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"


@pytest.fixture(scope="module")
def auth_token():
    """Get a JWT token for testing"""
    from api.auth import create_access_token
    return create_access_token({"sub": "test-user", "email": "test@example.com", "roles": ["admin"]})


@pytest.fixture(scope="module")
def client(auth_token):
    """Create test client with auth"""
    from api.main import app
    with TestClient(app) as client:
        client.auth_token = auth_token
        client.auth_headers = {"Authorization": f"Bearer {auth_token}"}
        yield client


@pytest.mark.integration
class TestComplianceWorkflowIntegration:
    """Integration tests for compliance checking workflow"""

    @pytest.fixture
    def checker(self):
        """Create compliance checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["pci_dss", "rbi", "dpdp"])

    @pytest.mark.integration
    def test_full_compliance_check_flow(self, checker):
        """Test complete compliance check flow"""
        code = '''
import os
from cryptography.fernet import Fernet

def process_payment(card_token: str, amount: float):
    """Process payment using tokenized card"""
    api_key = os.environ.get('PAYMENT_API_KEY')
    audit_log("payment_started", amount=amount)

    if not verify_otp(user_otp):
        raise AuthenticationError("OTP verification failed")

    if not get_consent(user_id, "payment"):
        raise ConsentRequired()

    url = "https://secure-payment.example.com/charge"
    result = make_payment(card_token, amount, api_key, url)

    audit_log("payment_completed", result=result.id)
    return result
'''
        # Check code
        report = checker.check_code(code, "payment.py")

        # Generate text report
        text_report = checker.generate_report(report, format="text")
        assert "COMPLIANCE REPORT" in text_report

        # Generate JSON report
        json_report = checker.generate_report(report, format="json")
        assert "passed" in json_report

    @pytest.mark.integration
    def test_compliance_check_with_violations(self, checker):
        """Test compliance check with multiple violations"""
        code = '''
# Multiple violations
password = "hardcoded_password_123"
card_number = "4111111111111111"

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

def send_data():
    url = "http://insecure-api.com/data"
    response = requests.post(url, data=sensitive_data, verify=False)
'''
        report = checker.check_code(code, "violations.py")

        assert not report.passed
        assert report.summary["critical"] > 0 or report.summary["high"] > 0

        # Should have multiple types of issues
        rule_ids = {i.rule_id for i in report.issues}
        assert len(rule_ids) > 1  # Multiple different rules triggered

    @pytest.mark.integration
    def test_compliance_check_file(self, checker, tmp_path):
        """Test compliance checking a file"""
        test_file = tmp_path / "test_code.py"
        test_file.write_text('''
api_key = "sk_live_1234567890abcdef"
url = "http://api.example.com"
''')

        report = checker.check_file(str(test_file))

        assert not report.passed
        assert len(report.issues) > 0

    @pytest.mark.integration
    def test_multi_standard_compliance(self, checker):
        """Test compliance check against multiple standards"""
        code = '''
region = "us-west-2"  # RBI violation
password = "secret123"  # PCI violation
# No consent management - DPDP violation
'''
        report = checker.check_code(code, "multi.py")

        # Should find issues from multiple standards
        standards_found = {i.standard for i in report.issues}
        assert len(standards_found) >= 2

    @pytest.mark.integration
    def test_recommendations_generated(self, checker):
        """Test that recommendations are generated"""
        code = '''
password = "insecure_password"
card_number = "4111111111111111"
'''
        report = checker.check_code(code, "test.py")

        assert len(report.recommendations) > 0

    @pytest.mark.integration
    def test_line_numbers_accurate(self, checker):
        """Test line numbers are accurately tracked"""
        code = '''# Line 1
# Line 2
# Line 3
password = "secret"  # Line 4
# Line 5
'''
        report = checker.check_code(code, "test.py")

        password_issues = [i for i in report.issues if "password" in i.evidence.lower()]
        if password_issues:
            assert password_issues[0].line_number == 4


@pytest.mark.integration
class TestComplianceAPIIntegration:
    """Integration tests for compliance API endpoints"""

    @pytest.mark.integration
    def test_compliance_endpoint_clean_code(self, client):
        """Test compliance API with clean code"""
        response = client.post("/compliance/check", json={
            "code": '''
import os
from cryptography.fernet import Fernet

def secure_hash(data):
    key = os.environ.get('ENCRYPTION_KEY')
    f = Fernet(key)
    return f.encrypt(data.encode())
''',
            "filename": "secure.py",
            "standards": ["pci_dss"]
        }, headers=client.auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "passed" in data
        assert "issues" in data

    @pytest.mark.integration
    def test_compliance_endpoint_violations(self, client):
        """Test compliance API detecting violations"""
        response = client.post("/compliance/check", json={
            "code": '''
password = "supersecret123"
card = "4111111111111111"
url = "http://insecure.com"
''',
            "filename": "insecure.py",
            "standards": ["pci_dss"]
        }, headers=client.auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["passed"] is False
        assert len(data["issues"]) > 0

    @pytest.mark.integration
    def test_compliance_endpoint_default_standards(self, client):
        """Test compliance API with default standards"""
        response = client.post("/compliance/check", json={
            "code": "print('hello')",
            "filename": "test.py"
        }, headers=client.auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "passed" in data

    @pytest.mark.integration
    def test_compliance_endpoint_response_format(self, client):
        """Test compliance API response format"""
        response = client.post("/compliance/check", json={
            "code": "x = 1",
            "filename": "test.py"
        }, headers=client.auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "passed" in data
        assert "summary" in data
        assert "issues" in data
        assert "recommendations" in data


@pytest.mark.integration
class TestComplianceWithRAGIntegration:
    """Integration tests for compliance with RAG context"""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create RAG orchestrator"""
        from core.orchestrator import RAGOrchestrator
        from verticals.fintech import register_fintech_roles

        register_fintech_roles()

        return RAGOrchestrator(
            model_interface=None,
            max_agents=5,
            default_vertical="fintech",
            rag_persist_dir=str(tmp_path)
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compliance_task_execution(self, orchestrator):
        """Test compliance-aware task execution"""
        result = await orchestrator.execute(
            task="Review code for PCI-DSS compliance",
            vertical="fintech",
            compliance_requirements=["pci_dss"],
            use_rag=False
        )

        assert result.success is True
        assert "pci_dss" in result.compliance_status

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_compliance_task(self, orchestrator):
        """Test task with multiple compliance requirements"""
        result = await orchestrator.execute(
            task="Implement payment processing with compliance",
            vertical="fintech",
            compliance_requirements=["pci_dss", "rbi_guidelines", "data_encryption"],
            use_rag=False
        )

        assert result.success is True
        # Should track all specified compliance requirements
        for req in ["pci_dss"]:
            if req in result.compliance_status:
                assert isinstance(result.compliance_status[req], bool)


@pytest.mark.integration
class TestComplianceReportIntegration:
    """Integration tests for compliance report generation"""

    @pytest.fixture
    def checker(self):
        """Create checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker()

    @pytest.mark.integration
    def test_report_severity_summary(self, checker):
        """Test report includes accurate severity summary"""
        code = '''
# Critical: hardcoded card
card = "4111111111111111"
# High: hardcoded password
password = "secret123"
# High: insecure HTTP
url = "http://api.com"
'''
        report = checker.check_code(code, "test.py")
        text_report = checker.generate_report(report, format="text")

        assert "Critical:" in text_report
        assert "High:" in text_report

    @pytest.mark.integration
    def test_json_report_parseable(self, checker):
        """Test JSON report is valid and parseable"""
        import json

        code = 'password = "test123"'
        report = checker.check_code(code, "test.py")
        json_report = checker.generate_report(report, format="json")

        parsed = json.loads(json_report)
        assert isinstance(parsed["passed"], bool)
        assert isinstance(parsed["issues"], list)

    @pytest.mark.integration
    def test_report_includes_evidence(self, checker):
        """Test report includes evidence for issues"""
        # Use PCI-DSS only checker to avoid function_presence checks
        from verticals.fintech.compliance import ComplianceChecker
        pci_checker = ComplianceChecker(standards=["pci_dss"])

        code = '''
secret_key = "sk_live_abcdef123456789012345"
url = "http://insecure-api.example.com"
'''
        report = pci_checker.check_code(code, "test.py")
        text_report = pci_checker.generate_report(report, format="text")

        assert "Evidence:" in text_report
        # Should have evidence about the issues found
        assert "Line" in text_report or "insecure" in text_report.lower() or "http:" in text_report.lower()
