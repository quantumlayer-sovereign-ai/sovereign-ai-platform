"""
Unit Tests for Agent Factory

Tests:
- Factory initialization
- Agent spawning
- Pool management
- Resource limits
- Cleanup
"""

from unittest.mock import Mock

import pytest


class TestAgentFactoryUnit:
    """Unit tests for AgentFactory class"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register FinTech roles before tests"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.mark.unit
    def test_factory_initialization(self):
        """Test factory initialization"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(max_agents=10)

        assert factory.max_agents == 10
        assert len(factory.active_agents) == 0

    @pytest.mark.unit
    def test_factory_with_model(self):
        """Test factory with model interface"""
        from core.agents.factory import AgentFactory

        mock_model = Mock()
        factory = AgentFactory(model_interface=mock_model, max_agents=5)

        assert factory.model_interface == mock_model

    @pytest.mark.unit
    def test_spawn_agent(self):
        """Test spawning an agent"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)
        agent = factory.spawn("coder")

        assert agent is not None
        assert agent.agent_id in factory.active_agents

        factory.destroy_all()

    @pytest.mark.unit
    def test_spawn_multiple_agents(self):
        """Test spawning multiple agents"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=10)
        agent1 = factory.spawn("coder")
        agent2 = factory.spawn("reviewer")

        assert len(factory.active_agents) == 2
        assert agent1.agent_id != agent2.agent_id

        factory.destroy_all()

    @pytest.mark.unit
    def test_spawn_at_limit(self):
        """Test spawning when at agent limit"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(max_agents=2)

        factory.spawn("coder")
        factory.spawn("reviewer")

        with pytest.raises(RuntimeError, match="Maximum agents"):
            factory.spawn("security")

        factory.destroy_all()

    @pytest.mark.unit
    def test_spawn_unknown_role(self):
        """Test spawning unknown role"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(max_agents=5)

        with pytest.raises(ValueError, match="Role not found"):
            factory.spawn("unknown_role_xyz")

    @pytest.mark.unit
    def test_spawn_for_task(self):
        """Test automatic spawning based on task"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=10)
        agents = factory.spawn_for_task("Write code for payment processing")

        assert len(agents) > 0

        factory.destroy_all()

    @pytest.mark.unit
    def test_get_agent(self):
        """Test getting agent by ID"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)
        agent = factory.spawn("coder")

        retrieved = factory.get_agent(agent.agent_id)

        assert retrieved == agent

        factory.destroy_all()

    @pytest.mark.unit
    def test_get_nonexistent_agent(self):
        """Test getting non-existent agent"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(max_agents=5)
        result = factory.get_agent("nonexistent")

        assert result is None

    @pytest.mark.unit
    def test_list_agents(self):
        """Test listing all agents"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)
        factory.spawn("coder")
        factory.spawn("reviewer")

        agents = factory.list_agents()

        assert len(agents) == 2
        for agent_info in agents:
            assert "id" in agent_info
            assert "role" in agent_info
            assert "state" in agent_info

        factory.destroy_all()

    @pytest.mark.unit
    def test_destroy_agent(self):
        """Test destroying an agent"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)
        agent = factory.spawn("coder")
        agent_id = agent.agent_id

        factory.destroy_agent(agent_id)

        assert agent_id not in factory.active_agents

    @pytest.mark.unit
    def test_destroy_all(self):
        """Test destroying all agents"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=10)
        factory.spawn("coder")
        factory.spawn("reviewer")
        factory.spawn("security")

        factory.destroy_all()

        assert len(factory.active_agents) == 0

    @pytest.mark.unit
    def test_factory_stats(self):
        """Test factory statistics"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)
        factory.spawn("coder")
        factory.spawn("reviewer")

        stats = factory.stats

        assert stats["active_agents"] == 2
        assert stats["max_agents"] == 5
        assert stats["total_spawned"] >= 2

        factory.destroy_all()

    @pytest.mark.unit
    def test_audit_trail(self):
        """Test getting audit trail"""
        from core.agents.factory import AgentFactory

        factory = AgentFactory(model_interface=None, max_agents=5)
        agent1 = factory.spawn("coder")
        factory.destroy_agent(agent1.agent_id)
        agent2 = factory.spawn("reviewer")

        trail = factory.get_audit_trail()

        # Should include both destroyed and active
        assert len(trail) >= 2

        factory.destroy_all()
