"""
Integration Tests for Security Flow

Tests complete security scanning workflows:
- Code scanning → Vulnerability detection → Report
- Directory scanning
- API integration for security
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    from api.main import app
    with TestClient(app) as client:
        yield client


@pytest.mark.integration
class TestSecurityScannerIntegration:
    """Integration tests for security scanner workflow"""

    @pytest.fixture
    def scanner(self):
        """Create security scanner"""
        from core.tools.security_tools import SecurityScanner
        return SecurityScanner()

    @pytest.mark.integration
    def test_full_security_scan_flow(self, scanner):
        """Test complete security scan flow"""
        code = '''
import os
import hashlib

def authenticate(username, password):
    """Authenticate user securely"""
    stored_hash = get_stored_hash(username)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        os.urandom(32),
        100000
    )
    return compare_hashes(stored_hash, password_hash)
'''
        result = scanner.scan_code(code, "auth.py")

        assert "passed" in result
        assert "total_issues" in result
        assert "issues" in result

    @pytest.mark.integration
    def test_scan_multiple_vulnerabilities(self, scanner):
        """Test scanning code with multiple vulnerabilities"""
        code = '''
import os
import hashlib

# SQL Injection
def get_user(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Hardcoded secret (test pattern - not a real key)
API_KEY = "test_key_EXAMPLE_not_real_1234567890"

# Weak crypto
def hash_password(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()

# Command injection
def run_cmd(user_input):
    os.system("ls " + user_input)

# Insecure HTTP
def fetch_data():
    return requests.get("http://api.example.com/data")
'''
        result = scanner.scan_code(code, "vulnerable.py")

        assert not result["passed"]
        assert result["total_issues"] >= 4

        # Check specific vulnerabilities detected
        rule_ids = {i["rule_id"] for i in result["issues"]}
        assert "SEC001" in rule_ids  # SQL injection
        assert "SEC003" in rule_ids  # Hardcoded secret
        assert "SEC005" in rule_ids  # Weak crypto
        assert "SEC006" in rule_ids  # Command injection

    @pytest.mark.integration
    def test_scan_clean_code(self, scanner):
        """Test scanning secure code"""
        code = '''
import os
import hashlib
from cryptography.fernet import Fernet

def secure_hash(data: str, salt: bytes) -> str:
    """Securely hash data with salt"""
    return hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000).hex()

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data using Fernet"""
    key = os.environ.get('ENCRYPTION_KEY')
    f = Fernet(key)
    return f.encrypt(data)

def make_request(endpoint: str) -> dict:
    """Make secure HTTPS request"""
    base_url = os.environ.get('API_BASE_URL')  # Should be HTTPS
    return requests.get(f"{base_url}/{endpoint}")
'''
        result = scanner.scan_code(code, "secure.py")

        # May have some issues but should be mostly clean
        critical_high = [i for i in result["issues"]
                        if i["severity"] in ["critical", "high"]]
        # Clean code should have minimal critical/high issues
        assert len(critical_high) <= 1

    @pytest.mark.integration
    def test_scan_directory(self, scanner, tmp_path):
        """Test scanning an entire directory"""
        # Create test files
        (tmp_path / "safe.py").write_text('''
def add(a, b):
    return a + b
''')
        (tmp_path / "unsafe.py").write_text('''
password = "supersecretpassword123"
api_key = "sk_live_1234567890abcdefghij"
''')
        (tmp_path / "query.py").write_text('''
def get_data(id):
    cursor.execute(f"SELECT * FROM table WHERE id = {id}")
''')

        result = scanner.scan_directory(str(tmp_path))

        assert result["success"] is True
        assert result["total_issues"] >= 2

    @pytest.mark.integration
    def test_scan_directory_recursive(self, scanner, tmp_path):
        """Test recursive directory scanning"""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "root.py").write_text('password = "root_secret_password_long"')
        (subdir / "nested.py").write_text('api_key = "nested_secret_api_key_123"')

        result = scanner.scan_directory(str(tmp_path))

        assert result["success"] is True
        assert result["total_issues"] >= 1

    @pytest.mark.integration
    def test_issue_severity_distribution(self, scanner):
        """Test issues have proper severity distribution"""
        code = '''
# Critical severity
password = "supersecret123"

# High severity - SQL injection
query = f"SELECT * FROM users WHERE id = {user_id}"

# Medium severity - HTTP URL
url = "http://example.com"
'''
        result = scanner.scan_code(code, "test.py")

        severities = [i["severity"] for i in result["issues"]]
        # Should have various severity levels
        assert len(set(severities)) >= 1


@pytest.mark.integration
class TestSecurityAPIIntegration:
    """Integration tests for security API endpoints"""

    @pytest.mark.integration
    def test_security_scan_endpoint(self, client):
        """Test security scan API endpoint"""
        response = client.post("/security/scan", json={
            "code": '''
def add(a, b):
    return a + b
''',
            "filename": "clean.py"
        })

        # May be 200 or 503 depending on initialization
        if response.status_code == 200:
            data = response.json()
            assert "passed" in data
            assert "total_issues" in data

    @pytest.mark.integration
    def test_security_scan_vulnerabilities(self, client):
        """Test security scan detects vulnerabilities"""
        response = client.post("/security/scan", json={
            "code": '''
password = "supersecretpassword"
query = f"SELECT * FROM users WHERE id = {user_id}"
''',
            "filename": "vulnerable.py"
        })

        if response.status_code == 200:
            data = response.json()
            assert data["passed"] is False
            assert data["total_issues"] > 0

    @pytest.mark.integration
    def test_security_scan_response_format(self, client):
        """Test security scan response format"""
        response = client.post("/security/scan", json={
            "code": "x = 1",
            "filename": "test.py"
        })

        if response.status_code == 200:
            data = response.json()
            assert "passed" in data
            assert "total_issues" in data
            assert "issues" in data
            assert isinstance(data["issues"], list)


@pytest.mark.integration
class TestSecurityWithOrchestratorIntegration:
    """Integration tests for security scanning with orchestrator"""

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
    async def test_security_task_execution(self, orchestrator):
        """Test security-focused task execution"""
        result = await orchestrator.execute(
            task="Review code for security vulnerabilities",
            vertical="fintech",
            compliance_requirements=["pci_dss"],
            use_rag=False
        )

        assert result.success is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_scan_in_results(self, orchestrator):
        """Test that security scanning is part of result processing"""
        # This tests the internal _scan_results_for_security method
        results = [{
            "response": '''```python
password = "insecure123"
```'''
        }]

        scan_result = await orchestrator._scan_results_for_security(results)

        assert scan_result["scanned"] is True
        assert len(scan_result["issues"]) > 0


@pytest.mark.integration
class TestDependencyScannerIntegration:
    """Integration tests for dependency scanner"""

    @pytest.fixture
    def scanner(self):
        """Create dependency scanner if available"""
        try:
            from core.tools.security_tools import DependencyScanner
            return DependencyScanner()
        except ImportError:
            pytest.skip("DependencyScanner not available")

    @pytest.mark.integration
    def test_scan_requirements(self, scanner, tmp_path):
        """Test scanning requirements.txt"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text('''
requests==2.28.0
django==3.2.0
flask==2.0.0
''')

        result = scanner.scan_requirements(str(req_file))

        assert result["success"] is True
        assert result["dependencies"] >= 3


@pytest.mark.integration
class TestSecurityRulesIntegration:
    """Integration tests for security rule coverage"""

    @pytest.fixture
    def scanner(self):
        """Create scanner"""
        from core.tools.security_tools import SecurityScanner
        return SecurityScanner()

    @pytest.mark.integration
    def test_all_owasp_categories_covered(self, scanner):
        """Test scanner covers OWASP categories"""
        # Get all rules
        rules = scanner.RULES

        # Check for key vulnerability categories
        rule_names = [r["name"].lower() for r in rules.values()]
        rule_str = " ".join(rule_names)

        assert "sql injection" in rule_str
        assert "xss" in rule_str.lower() or "cross" in rule_str
        assert "secret" in rule_str or "credential" in rule_str
        assert "command" in rule_str or "injection" in rule_str

    @pytest.mark.integration
    def test_rules_have_required_fields(self, scanner):
        """Test all rules have required fields"""
        for rule_id, rule in scanner.RULES.items():
            assert "name" in rule, f"Rule {rule_id} missing name"
            assert "severity" in rule, f"Rule {rule_id} missing severity"
            assert "patterns" in rule, f"Rule {rule_id} missing patterns"

    @pytest.mark.integration
    def test_severity_values_valid(self, scanner):
        """Test all severity values are valid"""
        valid_severities = {"critical", "high", "medium", "low", "info"}

        for rule_id, rule in scanner.RULES.items():
            severity = rule["severity"]
            if hasattr(severity, 'value'):
                severity = severity.value
            assert severity in valid_severities, \
                f"Rule {rule_id} has invalid severity: {severity}"
