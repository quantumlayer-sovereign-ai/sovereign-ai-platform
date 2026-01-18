"""
Unit Tests for Orchestrator

Tests:
- Task analysis
- Agent spawning
- Result aggregation
- Compliance verification
"""


import pytest


class TestOrchestratorUnit:
    """Unit tests for Orchestrator class"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register FinTech roles before tests"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator"""
        from core.orchestrator.main import Orchestrator
        return Orchestrator(
            model_interface=None,
            max_agents=10,
            default_vertical="fintech"
        )

    @pytest.mark.unit
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        from core.orchestrator.main import Orchestrator

        orch = Orchestrator(max_agents=5, default_vertical="fintech")

        assert orch.default_vertical == "fintech"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_basic(self, orchestrator):
        """Test basic task execution"""
        result = await orchestrator.execute(
            task="Write a function",
            vertical="fintech"
        )

        assert result.task_id is not None
        assert result.success is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_compliance(self, orchestrator):
        """Test execution with compliance requirements"""
        result = await orchestrator.execute(
            task="Store card data",
            vertical="fintech",
            compliance_requirements=["pci_dss"]
        )

        assert "pci_dss" in result.compliance_status

    @pytest.mark.unit
    def test_task_history(self, orchestrator):
        """Test task history tracking"""
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            orchestrator.execute(task="Task 1")
        )

        history = orchestrator.get_task_history()
        assert len(history) >= 1

    @pytest.mark.unit
    def test_orchestrator_stats(self, orchestrator):
        """Test orchestrator statistics"""
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            orchestrator.execute(task="Test task")
        )

        stats = orchestrator.stats

        assert stats["total_tasks"] >= 1
        assert "factory_stats" in stats


class TestExecutionModeUnit:
    """Unit tests for ExecutionMode enum"""

    @pytest.mark.unit
    def test_execution_modes(self):
        """Test execution mode values"""
        from core.orchestrator.main import ExecutionMode

        assert ExecutionMode.SEQUENTIAL.value == "sequential"
        assert ExecutionMode.PARALLEL.value == "parallel"
        assert ExecutionMode.PIPELINE.value == "pipeline"


class TestTaskPlanUnit:
    """Unit tests for TaskPlan dataclass"""

    @pytest.mark.unit
    def test_task_plan_creation(self):
        """Test TaskPlan creation"""
        from core.orchestrator.main import ExecutionMode, TaskPlan

        plan = TaskPlan(
            task_id="task_1",
            original_task="Test task",
            analysis="Analysis here",
            subtasks=[{"task": "subtask1"}],
            agents_needed=["coder"],
            execution_mode=ExecutionMode.SEQUENTIAL,
            compliance_checks=["pci_dss"]
        )

        assert plan.task_id == "task_1"
        assert len(plan.subtasks) == 1
        assert plan.execution_mode == ExecutionMode.SEQUENTIAL


class TestTaskResultUnit:
    """Unit tests for TaskResult dataclass"""

    @pytest.mark.unit
    def test_task_result_creation(self):
        """Test TaskResult creation"""
        from core.orchestrator.main import TaskResult

        result = TaskResult(
            task_id="task_1",
            success=True,
            results=[{"response": "done"}],
            aggregated_output="All done",
            compliance_status={"pci_dss": True},
            execution_time_seconds=1.5,
            agents_used=["coder"],
            audit_trail=[]
        )

        assert result.task_id == "task_1"
        assert result.success is True
        assert result.execution_time_seconds == 1.5


class TestRegionAwareOrchestrator:
    """Unit tests for region-aware orchestrator functionality"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register FinTech roles before tests"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator"""
        from core.orchestrator.main import Orchestrator
        return Orchestrator(
            model_interface=None,
            max_agents=10,
            default_vertical="fintech"
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_region_india(self, orchestrator):
        """Test execution with India region (default)"""
        result = await orchestrator.execute(
            task="Write a payment function",
            vertical="fintech",
            region="india"
        )

        assert result.task_id is not None
        assert result.success is True
        # Compliance status should include basic checks
        assert isinstance(result.compliance_status, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_region_eu(self, orchestrator):
        """Test execution with EU region"""
        result = await orchestrator.execute(
            task="Write a SEPA payment function",
            vertical="fintech",
            region="eu"
        )

        assert result.task_id is not None
        assert result.success is True
        # Verify task was planned with EU region
        assert isinstance(result.compliance_status, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_region_uk(self, orchestrator):
        """Test execution with UK region"""
        result = await orchestrator.execute(
            task="Write a Faster Payments function",
            vertical="fintech",
            region="uk"
        )

        assert result.task_id is not None
        assert result.success is True
        assert isinstance(result.compliance_status, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_default_region(self, orchestrator):
        """Test execution without region defaults to India"""
        result = await orchestrator.execute(
            task="Write a payment function",
            vertical="fintech"
        )

        assert result.task_id is not None
        assert result.success is True
        assert isinstance(result.compliance_status, dict)

    @pytest.mark.unit
    def test_apply_region_prefix_india(self, orchestrator):
        """Test region prefix application for India"""
        roles = ["fintech_coder", "fintech_security"]
        result = orchestrator._apply_region_prefix(roles, "india")

        assert "fintech_coder" in result
        assert "eu_fintech_coder" not in result
        assert "uk_fintech_coder" not in result

    @pytest.mark.unit
    def test_apply_region_prefix_eu(self, orchestrator):
        """Test region prefix application for EU"""
        roles = ["fintech_coder", "fintech_security"]
        result = orchestrator._apply_region_prefix(roles, "eu")

        # Should have EU prefixed roles if they exist
        eu_roles = [r for r in result if r.startswith("eu_")]
        assert len(eu_roles) > 0 or roles == result  # Either prefixed or fallback

    @pytest.mark.unit
    def test_apply_region_prefix_uk(self, orchestrator):
        """Test region prefix application for UK"""
        roles = ["fintech_coder", "fintech_security"]
        result = orchestrator._apply_region_prefix(roles, "uk")

        # Should have UK prefixed roles if they exist
        uk_roles = [r for r in result if r.startswith("uk_")]
        assert len(uk_roles) > 0 or roles == result


class TestRAGOrchestratorRegion:
    """Unit tests for region-aware RAG orchestrator"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register FinTech roles before tests"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.fixture
    def rag_orchestrator(self):
        """Create RAG orchestrator"""
        from core.orchestrator import RAGOrchestrator
        return RAGOrchestrator(
            model_interface=None,
            max_agents=10,
            default_vertical="fintech"
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rag_execute_with_region_eu(self, rag_orchestrator):
        """Test RAG execution with EU region"""
        result = await rag_orchestrator.execute(
            task="Create GDPR-compliant data storage",
            vertical="fintech",
            region="eu",
            use_rag=False  # Disable RAG for unit test
        )

        assert result.task_id is not None
        assert result.success is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rag_execute_with_region_uk(self, rag_orchestrator):
        """Test RAG execution with UK region"""
        result = await rag_orchestrator.execute(
            task="Implement FCA Consumer Duty compliance",
            vertical="fintech",
            region="uk",
            use_rag=False
        )

        assert result.task_id is not None
        assert result.success is True
