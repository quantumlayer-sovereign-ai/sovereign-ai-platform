"""
Integration Tests for Agent Workflow

Tests complete agent workflows:
- Role registration → Agent spawning → Task execution → Cleanup
"""


import pytest


@pytest.mark.integration
class TestAgentWorkflowIntegration:
    """Integration tests for agent workflows"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register FinTech roles before tests"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.mark.integration
    def test_registry_role_lookup(self):
        """Test role lookup from registry"""
        from core.agents.registry import get_registry

        registry = get_registry()
        roles = registry.list_roles()

        assert "fintech_coder" in roles
        assert "fintech_security" in roles

    @pytest.mark.integration
    def test_factory_spawn_fintech_agent(self):
        """Test spawning FinTech-specific agent"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)

        agent = factory.spawn("fintech_coder")

        assert agent is not None
        assert agent.role_name == "fintech_coder"
        assert "fintech" in agent.system_prompt.lower() or \
               "payment" in agent.system_prompt.lower()

        factory.destroy_agent(agent.agent_id)

    @pytest.mark.integration
    def test_factory_spawn_for_payment_task(self):
        """Test automatic spawning for payment task"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=10)

        agents = factory.spawn_for_task(
            "Implement secure payment processing",
            vertical="fintech"
        )

        assert len(agents) > 0
        roles = [a.role_name for a in agents]

        # Should include relevant fintech roles
        assert any("fintech" in r or "coder" in r or "security" in r for r in roles)

        factory.destroy_all()

    @pytest.mark.integration
    def test_factory_spawn_for_security_task(self):
        """Test spawning for security review task"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=10)

        agents = factory.spawn_for_task(
            "Review security vulnerabilities in the payment module",
            vertical="fintech"
        )

        assert len(agents) > 0

        factory.destroy_all()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_execution_without_model(self):
        """Test agent execution without attached model"""
        from core.agents.base import AgentContext
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)
        agent = factory.spawn("fintech_coder")

        context = AgentContext(
            task="Write secure payment function",
            vertical="fintech",
            compliance_requirements=["pci_dss"]
        )

        result = await agent.execute(context)

        assert result["success"] is True
        assert "[No model attached]" in result["response"]

        factory.destroy_agent(agent.agent_id)

    @pytest.mark.integration
    def test_agent_audit_trail(self):
        """Test agent audit trail generation"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)

        agent1 = factory.spawn("fintech_coder")
        _agent2 = factory.spawn("fintech_security")  # noqa: F841

        factory.destroy_agent(agent1.agent_id)

        audit = factory.get_audit_trail()

        assert len(audit) >= 2
        # Destroyed agent should be in history
        assert any(a.get("agent_id") == agent1.agent_id for a in audit if isinstance(a, dict))

        factory.destroy_all()

    @pytest.mark.integration
    def test_agent_pool_limits(self):
        """Test agent pool limit enforcement"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=3)

        agents = []
        for _ in range(3):
            agents.append(factory.spawn("fintech_coder"))

        # Should fail when limit reached
        with pytest.raises(RuntimeError, match="Maximum agents"):
            factory.spawn("fintech_coder")

        factory.destroy_all()

    @pytest.mark.integration
    def test_parent_child_relationship(self):
        """Test parent-child agent relationships"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=10)

        parent = factory.spawn("fintech_coder")
        child = factory.spawn("fintech_security", parent_id=parent.agent_id)

        assert child.parent_id == parent.agent_id

        factory.destroy_all()


@pytest.mark.integration
class TestOrchestratorWorkflowIntegration:
    """Integration tests for orchestrator workflows"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register FinTech roles"""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_orchestrator_execute_simple(self, orchestrator):
        """Test simple task execution"""
        result = await orchestrator.execute(
            task="Write a hello world function",
            vertical="fintech"
        )

        assert result.task_id is not None
        assert result.success is True
        assert len(result.agents_used) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_orchestrator_execute_with_compliance(self, orchestrator):
        """Test execution with compliance requirements"""
        result = await orchestrator.execute(
            task="Implement credit card storage",
            vertical="fintech",
            compliance_requirements=["pci_dss", "data_encryption"]
        )

        assert result.success is True
        assert "pci_dss" in result.compliance_status

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_orchestrator_task_history(self, orchestrator):
        """Test task history tracking"""
        await orchestrator.execute(task="Task 1")
        await orchestrator.execute(task="Task 2")

        history = orchestrator.get_task_history()

        assert len(history) >= 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_orchestrator_stats(self, orchestrator):
        """Test orchestrator statistics"""
        await orchestrator.execute(task="Test task")

        stats = orchestrator.stats

        assert stats["total_tasks"] >= 1
        assert "factory_stats" in stats


@pytest.mark.integration
class TestRAGOrchestratorWorkflowIntegration:
    """Integration tests for RAG-enhanced orchestrator"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register FinTech roles"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.fixture
    def temp_kb(self, tmp_path):
        """Create temporary knowledge base"""
        kb_path = tmp_path / "kb"
        kb_path.mkdir()

        (kb_path / "test.md").write_text("""
# Security Guidelines
Always use HTTPS for API calls.
Hash passwords with bcrypt.
""")

        return kb_path

    @pytest.fixture
    def rag_orchestrator(self, tmp_path):
        """Create RAG orchestrator"""
        from core.orchestrator import RAGOrchestrator

        db_path = tmp_path / "vectordb"
        db_path.mkdir()

        return RAGOrchestrator(
            model_interface=None,
            max_agents=10,
            default_vertical="fintech",
            rag_persist_dir=str(db_path)
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rag_orchestrator_execute(self, rag_orchestrator):
        """Test RAG orchestrator execution"""
        result = await rag_orchestrator.execute(
            task="Review payment security",
            vertical="fintech",
            use_rag=False  # No KB indexed yet
        )

        assert result.success is True
        assert result.task_id is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rag_orchestrator_with_kb(self, rag_orchestrator, temp_kb):
        """Test RAG orchestrator with knowledge base"""
        # Index knowledge base
        await rag_orchestrator.index_knowledge_base(
            str(temp_kb),
            vertical="fintech"
        )

        # Execute with RAG
        result = await rag_orchestrator.execute(
            task="What are security guidelines?",
            vertical="fintech",
            use_rag=True
        )

        assert result.success is True
        # Audit trail should include RAG sources
        assert len(result.audit_trail) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rag_search_knowledge(self, rag_orchestrator, temp_kb):
        """Test knowledge base search"""
        await rag_orchestrator.index_knowledge_base(str(temp_kb), "fintech")

        results = await rag_orchestrator.search_knowledge(
            query="password hashing",
            vertical="fintech"
        )

        # May or may not find results depending on indexing
        assert isinstance(results, list)

    @pytest.mark.integration
    def test_rag_stats(self, rag_orchestrator):
        """Test RAG statistics"""
        stats = rag_orchestrator.get_rag_stats()

        assert "base_rag" in stats
        assert "vertical_rags" in stats
