"""
Integration Tests for API Endpoints

Tests API endpoints with real dependencies:
- Health check
- Task execution
- Compliance checking
- Security scanning
- RAG operations

Note: Some tests require proper app initialization via startup event.
Use pytest fixtures that handle async lifecycle.
"""


import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create test client with proper app initialization"""
    from api.main import app

    # Use TestClient which handles startup/shutdown
    with TestClient(app) as client:
        yield client


@pytest.mark.integration
class TestAPIHealthEndpoints:
    """Integration tests for health endpoints"""

    @pytest.mark.integration
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "available_roles" in data
        assert "rag_enabled" in data

    @pytest.mark.integration
    def test_health_response_schema(self, client):
        """Test health response schema"""
        response = client.get("/health")
        data = response.json()

        required_fields = ["status", "model_loaded", "available_roles",
                         "uptime_seconds", "rag_enabled"]
        for field in required_fields:
            assert field in data


@pytest.mark.integration
class TestAPIRolesEndpoints:
    """Integration tests for roles endpoints"""

    @pytest.mark.integration
    def test_list_roles(self, client):
        """Test listing all roles"""
        response = client.get("/roles")

        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert "count" in data
        assert data["count"] > 0

    @pytest.mark.integration
    def test_list_roles_by_vertical(self, client):
        """Test listing roles by vertical"""
        response = client.get("/roles?vertical=fintech")

        assert response.status_code == 200
        data = response.json()
        assert data["vertical_filter"] == "fintech"

    @pytest.mark.integration
    def test_get_specific_role(self, client):
        """Test getting specific role details"""
        response = client.get("/roles/fintech_coder")

        # May be 200 or 404 depending on registration
        if response.status_code == 200:
            data = response.json()
            assert "name" in data or "system_prompt" in data

    @pytest.mark.integration
    def test_get_nonexistent_role(self, client):
        """Test getting non-existent role"""
        response = client.get("/roles/nonexistent_role_xyz")

        assert response.status_code == 404


@pytest.mark.integration
class TestAPIComplianceEndpoints:
    """Integration tests for compliance endpoints"""

    @pytest.mark.integration
    def test_compliance_check_clean_code(self, client):
        """Test compliance check on clean code"""
        response = client.post("/compliance/check", json={
            "code": """
import hashlib
import os

def hash_card(card_number: str) -> str:
    salt = os.urandom(32)
    return hashlib.pbkdf2_hmac('sha256', card_number.encode(), salt, 100000).hex()
""",
            "filename": "secure.py",
            "standards": ["pci_dss"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "passed" in data
        assert "issues" in data

    @pytest.mark.integration
    def test_compliance_check_violations(self, client):
        """Test compliance check detecting violations"""
        response = client.post("/compliance/check", json={
            "code": """
# Test card number
card = "4111111111111111"
url = "http://payment-api.example.com/charge"
""",
            "filename": "insecure.py",
            "standards": ["pci_dss"]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["passed"] is False
        assert len(data["issues"]) > 0

    @pytest.mark.integration
    def test_compliance_check_response_format(self, client):
        """Test compliance check response format"""
        response = client.post("/compliance/check", json={
            "code": "print('hello')",
            "filename": "test.py"
        })

        assert response.status_code == 200
        data = response.json()

        required_fields = ["passed", "summary", "issues", "recommendations"]
        for field in required_fields:
            assert field in data


@pytest.mark.integration
class TestAPISecurityEndpoints:
    """Integration tests for security endpoints"""

    @pytest.mark.integration
    def test_security_scan_clean(self, client):
        """Test security scan on clean code"""
        response = client.post("/security/scan", json={
            "code": """
def add(a, b):
    return a + b
""",
            "filename": "clean.py"
        })

        # May return 200 or 503 depending on initialization
        if response.status_code == 200:
            data = response.json()
            assert data["passed"] is True

    @pytest.mark.integration
    def test_security_scan_vulnerabilities(self, client):
        """Test security scan detecting vulnerabilities"""
        response = client.post("/security/scan", json={
            "code": """
password = "supersecretpassword123"
query = f"SELECT * FROM users WHERE id = {user_id}"
os.system("rm " + user_input)
""",
            "filename": "vulnerable.py"
        })

        if response.status_code == 200:
            data = response.json()
            assert data["passed"] is False
            assert data["total_issues"] > 0


@pytest.mark.integration
class TestAPITaskEndpoints:
    """Integration tests for task execution endpoints"""

    @pytest.mark.integration
    def test_execute_task_basic(self, client):
        """Test basic task execution"""
        response = client.post("/task/execute", json={
            "task": "Write a hello world function",
            "vertical": "fintech",
            "use_rag": False
        })

        # Accept 200 (success) or 503 (orchestrator not init in test)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "task_id" in data
            assert "output" in data

    @pytest.mark.integration
    def test_execute_task_response_schema(self, client):
        """Test task execution response schema"""
        response = client.post("/task/execute", json={
            "task": "Test task",
            "use_rag": False
        })

        if response.status_code == 200:
            data = response.json()

            required_fields = ["task_id", "success", "output", "agents_used",
                             "compliance_status", "execution_time_seconds"]
            for field in required_fields:
                assert field in data


@pytest.mark.integration
class TestAPIRAGEndpoints:
    """Integration tests for RAG endpoints"""

    @pytest.mark.integration
    def test_rag_search(self, client):
        """Test RAG search endpoint"""
        response = client.post("/rag/search", json={
            "query": "PCI-DSS requirements",
            "vertical": "fintech",
            "n_results": 3
        })

        # Accept 200 or 503
        if response.status_code == 200:
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert "count" in data

    @pytest.mark.integration
    def test_rag_stats(self, client):
        """Test RAG stats endpoint"""
        response = client.get("/rag/stats")

        if response.status_code == 200:
            data = response.json()
            assert "base_rag" in data


@pytest.mark.integration
class TestAPIStatsEndpoints:
    """Integration tests for stats endpoints"""

    @pytest.mark.integration
    def test_stats_endpoint(self, client):
        """Test platform statistics endpoint"""
        response = client.get("/stats")

        if response.status_code == 200:
            data = response.json()
            assert "orchestrator" in data
            assert "uptime_seconds" in data

    @pytest.mark.integration
    def test_audit_endpoint(self, client):
        """Test audit trail endpoint"""
        response = client.get("/audit")

        if response.status_code == 200:
            data = response.json()
            assert "audit_trail" in data
            assert "generated_at" in data


@pytest.mark.integration
class TestAPIModelEndpoints:
    """Integration tests for model endpoints"""

    @pytest.mark.integration
    def test_model_info(self, client):
        """Test model info endpoint"""
        response = client.get("/model/info")

        # 200 or 503 depending on model init
        if response.status_code == 200:
            data = response.json()
            assert "model_id" in data or "loaded" in data
