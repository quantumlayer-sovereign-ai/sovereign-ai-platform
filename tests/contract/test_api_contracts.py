"""
Contract Tests for API Schemas

Tests API request/response contracts:
- Pydantic model validation
- Request schema validation
- Response schema validation
- OpenAPI spec compliance
"""


import pytest
from pydantic import ValidationError


@pytest.mark.contract
class TestRequestSchemas:
    """Contract tests for API request schemas"""

    @pytest.mark.contract
    def test_task_request_valid(self):
        """Test valid TaskRequest"""
        from api.main import TaskRequest

        request = TaskRequest(
            task="Write secure payment code",
            vertical="fintech",
            compliance_requirements=["pci_dss"],
            use_rag=True
        )

        assert request.task == "Write secure payment code"
        assert request.vertical == "fintech"
        assert request.use_rag is True

    @pytest.mark.contract
    def test_task_request_minimal(self):
        """Test TaskRequest with minimal fields"""
        from api.main import TaskRequest

        request = TaskRequest(task="Simple task")

        assert request.task == "Simple task"
        assert request.vertical == "fintech"  # Default
        assert request.use_rag is True  # Default

    @pytest.mark.contract
    def test_task_request_empty_task_fails(self):
        """Test TaskRequest rejects empty task"""
        from api.main import TaskRequest

        with pytest.raises(ValidationError):
            TaskRequest(task="")

    @pytest.mark.contract
    def test_compliance_request_valid(self):
        """Test valid ComplianceRequest"""
        from api.main import ComplianceRequest

        request = ComplianceRequest(
            code="def hello(): pass",
            filename="test.py",
            standards=["pci_dss", "rbi"]
        )

        assert request.code == "def hello(): pass"
        assert request.filename == "test.py"

    @pytest.mark.contract
    def test_compliance_request_defaults(self):
        """Test ComplianceRequest default values"""
        from api.main import ComplianceRequest

        request = ComplianceRequest(code="print('hello')")

        assert request.filename == "code.py"
        # standards defaults to None (auto-detected from region by endpoint)
        assert request.standards is None
        assert request.region == "india"  # Default region

    @pytest.mark.contract
    def test_rag_index_request_valid(self):
        """Test valid RAGIndexRequest"""
        from api.main import RAGIndexRequest

        request = RAGIndexRequest(
            directory="/path/to/docs",
            vertical="fintech"
        )

        assert request.directory == "/path/to/docs"
        assert request.vertical == "fintech"

    @pytest.mark.contract
    def test_rag_search_request_valid(self):
        """Test valid RAGSearchRequest"""
        from api.main import RAGSearchRequest

        request = RAGSearchRequest(
            query="PCI-DSS requirements",
            vertical="fintech",
            n_results=5
        )

        assert request.query == "PCI-DSS requirements"
        assert request.n_results == 5

    @pytest.mark.contract
    def test_security_scan_request_valid(self):
        """Test valid SecurityScanRequest"""
        from api.main import SecurityScanRequest

        request = SecurityScanRequest(
            code="password = 'secret'",
            filename="config.py"
        )

        assert request.code == "password = 'secret'"
        assert request.filename == "config.py"


@pytest.mark.contract
class TestResponseSchemas:
    """Contract tests for API response schemas"""

    @pytest.mark.contract
    def test_task_response_valid(self):
        """Test valid TaskResponse"""
        from api.main import TaskResponse

        response = TaskResponse(
            task_id="task_123",
            success=True,
            output="Generated code here",
            agents_used=["coder", "reviewer"],
            compliance_status={"pci_dss": True},
            execution_time_seconds=1.5
        )

        assert response.task_id == "task_123"
        assert response.success is True
        assert len(response.agents_used) == 2

    @pytest.mark.contract
    def test_task_response_required_fields(self):
        """Test TaskResponse requires all fields"""
        from api.main import TaskResponse

        with pytest.raises(ValidationError):
            TaskResponse(
                task_id="task_123",
                success=True
                # Missing required fields
            )

    @pytest.mark.contract
    def test_health_response_valid(self):
        """Test valid HealthResponse"""
        from api.main import HealthResponse

        response = HealthResponse(
            status="healthy",
            model_loaded=True,
            available_roles=10,
            uptime_seconds=100.5,
            rag_enabled=True
        )

        assert response.status == "healthy"
        assert response.model_loaded is True

    @pytest.mark.contract
    def test_health_response_types(self):
        """Test HealthResponse field types"""
        from api.main import HealthResponse

        response = HealthResponse(
            status="healthy",
            model_loaded=False,
            available_roles=5,
            uptime_seconds=50.0
        )

        assert isinstance(response.status, str)
        assert isinstance(response.model_loaded, bool)
        assert isinstance(response.available_roles, int)
        assert isinstance(response.uptime_seconds, float)


@pytest.mark.contract
class TestSchemaSerializability:
    """Contract tests for schema JSON serialization"""

    @pytest.mark.contract
    def test_task_request_json_serializable(self):
        """Test TaskRequest can be serialized to JSON"""
        import json

        from api.main import TaskRequest

        request = TaskRequest(
            task="Test task",
            vertical="fintech",
            compliance_requirements=["pci_dss"]
        )

        json_str = request.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["task"] == "Test task"
        assert parsed["vertical"] == "fintech"

    @pytest.mark.contract
    def test_task_response_json_serializable(self):
        """Test TaskResponse can be serialized to JSON"""
        import json

        from api.main import TaskResponse

        response = TaskResponse(
            task_id="task_1",
            success=True,
            output="Output",
            agents_used=["coder"],
            compliance_status={"pci_dss": True},
            execution_time_seconds=1.0
        )

        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["task_id"] == "task_1"
        assert parsed["success"] is True


@pytest.mark.contract
class TestSchemaValidation:
    """Contract tests for schema validation rules"""

    @pytest.mark.contract
    def test_task_min_length(self):
        """Test task minimum length validation"""
        from api.main import TaskRequest

        # Single character should be valid
        request = TaskRequest(task="A")
        assert request.task == "A"

        # Empty should fail
        with pytest.raises(ValidationError):
            TaskRequest(task="")

    @pytest.mark.contract
    def test_compliance_requirements_list(self):
        """Test compliance_requirements accepts list"""
        from api.main import TaskRequest

        request = TaskRequest(
            task="Test",
            compliance_requirements=["pci_dss", "rbi", "gdpr"]
        )

        assert len(request.compliance_requirements) == 3

    @pytest.mark.contract
    def test_compliance_requirements_default_empty(self):
        """Test compliance_requirements defaults to empty list"""
        from api.main import TaskRequest

        request = TaskRequest(task="Test")

        assert request.compliance_requirements == []

    @pytest.mark.contract
    def test_n_results_default(self):
        """Test n_results default value"""
        from api.main import RAGSearchRequest

        request = RAGSearchRequest(
            query="test query",
            vertical="fintech"
        )

        assert request.n_results == 5


@pytest.mark.contract
class TestOpenAPICompliance:
    """Contract tests for OpenAPI spec compliance"""

    @pytest.fixture
    def openapi_schema(self):
        """Get OpenAPI schema from app"""
        from api.main import app
        return app.openapi()

    @pytest.mark.contract
    def test_openapi_has_info(self, openapi_schema):
        """Test OpenAPI has info section"""
        assert "info" in openapi_schema
        assert "title" in openapi_schema["info"]
        assert "version" in openapi_schema["info"]

    @pytest.mark.contract
    def test_openapi_has_paths(self, openapi_schema):
        """Test OpenAPI has paths"""
        assert "paths" in openapi_schema

        expected_paths = [
            "/health",
            "/task/execute",
            "/compliance/check",
            "/security/scan",
            "/rag/search"
        ]

        for path in expected_paths:
            assert path in openapi_schema["paths"], f"Missing path: {path}"

    @pytest.mark.contract
    def test_openapi_has_components(self, openapi_schema):
        """Test OpenAPI has components"""
        assert "components" in openapi_schema
        assert "schemas" in openapi_schema["components"]

    @pytest.mark.contract
    def test_openapi_task_request_schema(self, openapi_schema):
        """Test TaskRequest in OpenAPI schema"""
        schemas = openapi_schema["components"]["schemas"]

        assert "TaskRequest" in schemas
        task_schema = schemas["TaskRequest"]

        assert "properties" in task_schema
        assert "task" in task_schema["properties"]

    @pytest.mark.contract
    def test_openapi_task_response_schema(self, openapi_schema):
        """Test TaskResponse in OpenAPI schema"""
        schemas = openapi_schema["components"]["schemas"]

        assert "TaskResponse" in schemas
        response_schema = schemas["TaskResponse"]

        required_properties = ["task_id", "success", "output"]
        for prop in required_properties:
            assert prop in response_schema["properties"]

    @pytest.mark.contract
    def test_endpoints_have_responses(self, openapi_schema):
        """Test all endpoints have response definitions"""
        paths = openapi_schema["paths"]

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete"]:
                    assert "responses" in details, \
                        f"{method.upper()} {path} missing responses"
                    assert "200" in details["responses"] or \
                           "201" in details["responses"], \
                        f"{method.upper()} {path} missing success response"


@pytest.mark.contract
class TestDataTypes:
    """Contract tests for data type consistency"""

    @pytest.mark.contract
    def test_execution_time_is_float(self):
        """Test execution_time_seconds is always float"""
        from api.main import TaskResponse

        response = TaskResponse(
            task_id="task_1",
            success=True,
            output="Done",
            agents_used=[],
            compliance_status={},
            execution_time_seconds=1  # Integer input
        )

        assert isinstance(response.execution_time_seconds, float)

    @pytest.mark.contract
    def test_agents_used_is_list_of_strings(self):
        """Test agents_used is list of strings"""
        from api.main import TaskResponse

        response = TaskResponse(
            task_id="task_1",
            success=True,
            output="Done",
            agents_used=["coder", "reviewer", "security"],
            compliance_status={},
            execution_time_seconds=1.0
        )

        assert isinstance(response.agents_used, list)
        for agent in response.agents_used:
            assert isinstance(agent, str)

    @pytest.mark.contract
    def test_compliance_status_is_dict(self):
        """Test compliance_status is dict with bool values"""
        from api.main import TaskResponse

        response = TaskResponse(
            task_id="task_1",
            success=True,
            output="Done",
            agents_used=[],
            compliance_status={"pci_dss": True, "gdpr": False},
            execution_time_seconds=1.0
        )

        assert isinstance(response.compliance_status, dict)
        for key, value in response.compliance_status.items():
            assert isinstance(key, str)
            assert isinstance(value, bool)
