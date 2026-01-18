"""
Unit Tests for Role Registry

Tests:
- Registry initialization
- Built-in roles
- Custom role loading
- Role lookup and matching
- Role registration
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest


class TestRoleRegistryUnit:
    """Unit tests for RoleRegistry class"""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance"""
        from core.agents.registry import RoleRegistry
        return RoleRegistry()

    @pytest.fixture
    def isolated_registry(self, tmp_path):
        """Create registry with isolated roles directory"""
        from core.agents.registry import RoleRegistry
        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        return RoleRegistry(roles_dir=roles_dir)

    @pytest.mark.unit
    def test_registry_initialization(self, registry):
        """Test registry initializes with built-in roles"""
        assert registry is not None
        assert len(registry.roles) > 0

    @pytest.mark.unit
    def test_builtin_roles_exist(self, registry):
        """Test all built-in roles are present"""
        expected_roles = [
            "orchestrator",
            "architect",
            "coder",
            "reviewer",
            "tester",
            "devops",
            "documenter",
            "security"
        ]
        for role in expected_roles:
            assert role in registry.roles, f"Missing built-in role: {role}"

    @pytest.mark.unit
    def test_get_role_existing(self, registry):
        """Test getting an existing role"""
        role = registry.get_role("coder")

        assert role is not None
        assert role["name"] == "coder"
        assert "system_prompt" in role
        assert "tools" in role
        assert "spawn_conditions" in role

    @pytest.mark.unit
    def test_get_role_nonexistent(self, registry):
        """Test getting a non-existent role returns None"""
        role = registry.get_role("nonexistent_role_xyz")

        assert role is None

    @pytest.mark.unit
    def test_list_roles(self, registry):
        """Test listing all roles"""
        roles = registry.list_roles()

        assert isinstance(roles, list)
        assert len(roles) >= 8  # At least built-in roles
        assert "coder" in roles
        assert "reviewer" in roles

    @pytest.mark.unit
    def test_register_role(self, registry):
        """Test registering a new role"""
        new_role = {
            "name": "custom_role",
            "description": "A custom test role",
            "system_prompt": "You are a custom assistant.",
            "tools": ["custom_tool"],
            "spawn_conditions": ["custom"],
            "vertical": "test"
        }

        registry.register_role("custom_role", new_role)

        assert "custom_role" in registry.roles
        assert registry.get_role("custom_role") == new_role

    @pytest.mark.unit
    def test_find_roles_for_task_code(self, registry):
        """Test finding roles for a code-related task"""
        matching = registry.find_roles_for_task("Implement a new feature in code")

        assert "coder" in matching

    @pytest.mark.unit
    def test_find_roles_for_task_security(self, registry):
        """Test finding roles for a security task"""
        matching = registry.find_roles_for_task("Review for security vulnerabilities")

        assert "security" in matching or "reviewer" in matching

    @pytest.mark.unit
    def test_find_roles_for_task_deploy(self, registry):
        """Test finding roles for deployment task"""
        matching = registry.find_roles_for_task("Deploy to kubernetes")

        assert "devops" in matching

    @pytest.mark.unit
    def test_find_roles_for_task_test(self, registry):
        """Test finding roles for testing task"""
        matching = registry.find_roles_for_task("Write tests for the module")

        assert "tester" in matching

    @pytest.mark.unit
    def test_find_roles_for_task_no_match(self, registry):
        """Test finding roles with no matching conditions"""
        matching = registry.find_roles_for_task("random gibberish xyz123")

        # May return empty or some roles based on loose matching
        assert isinstance(matching, list)

    @pytest.mark.unit
    def test_find_roles_with_vertical_filter(self, registry):
        """Test finding roles with vertical filter"""
        # Register a vertical-specific role
        registry.register_role("fintech_test", {
            "name": "fintech_test",
            "spawn_conditions": ["payment"],
            "vertical": "fintech"
        })

        matching = registry.find_roles_for_task("Process payment", vertical="fintech")

        assert "fintech_test" in matching

    @pytest.mark.unit
    def test_find_roles_vertical_mismatch(self, registry):
        """Test that vertical filter excludes mismatched roles"""
        registry.register_role("healthcare_role", {
            "name": "healthcare_role",
            "spawn_conditions": ["diagnose"],
            "vertical": "healthcare"
        })

        matching = registry.find_roles_for_task("diagnose patient", vertical="fintech")

        assert "healthcare_role" not in matching

    @pytest.mark.unit
    def test_get_roles_by_vertical(self, registry):
        """Test getting roles by vertical"""
        # All built-in roles have vertical=None, so they should be returned
        roles = registry.get_roles_by_vertical("fintech")

        # Should include roles with vertical=None (matches any) or vertical=fintech
        assert len(roles) >= 8  # At least built-in roles

    @pytest.mark.unit
    def test_role_structure(self, registry):
        """Test that roles have required structure"""
        for role_name in registry.list_roles():
            role = registry.get_role(role_name)

            assert "name" in role
            assert role["name"] == role_name
            # These may or may not be present depending on role
            # Just check they're accessible
            _ = role.get("system_prompt")
            _ = role.get("tools")
            _ = role.get("spawn_conditions")

    @pytest.mark.unit
    def test_save_role(self, isolated_registry, tmp_path):
        """Test saving a role to YAML file"""
        isolated_registry.register_role("save_test", {
            "name": "save_test",
            "description": "Test role for saving",
            "system_prompt": "Test prompt"
        })

        isolated_registry.save_role("save_test")

        saved_file = tmp_path / "roles" / "save_test.yaml"
        assert saved_file.exists()

    @pytest.mark.unit
    def test_save_role_nonexistent(self, isolated_registry):
        """Test saving non-existent role raises error"""
        with pytest.raises(ValueError, match="Role not found"):
            isolated_registry.save_role("nonexistent_role")

    @pytest.mark.unit
    def test_load_custom_roles_from_yaml(self, tmp_path):
        """Test loading custom roles from YAML files"""
        from core.agents.registry import RoleRegistry

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()

        # Create a custom role YAML
        yaml_content = """
role:
  name: yaml_test_role
  description: A role loaded from YAML
  system_prompt: You are a test assistant.
  tools:
    - test_tool
  spawn_conditions:
    - yaml_test
"""
        (roles_dir / "yaml_test_role.yaml").write_text(yaml_content)

        registry = RoleRegistry(roles_dir=roles_dir)

        assert "yaml_test_role" in registry.roles
        role = registry.get_role("yaml_test_role")
        assert role["description"] == "A role loaded from YAML"

    @pytest.mark.unit
    def test_load_invalid_yaml(self, tmp_path):
        """Test handling of invalid YAML files"""
        from core.agents.registry import RoleRegistry

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()

        # Create invalid YAML
        (roles_dir / "invalid.yaml").write_text("invalid: yaml: content: [")

        # Should not raise, just log error and continue
        registry = RoleRegistry(roles_dir=roles_dir)
        assert registry is not None

    @pytest.mark.unit
    def test_load_yaml_without_role_key(self, tmp_path):
        """Test handling YAML without 'role' key"""
        from core.agents.registry import RoleRegistry

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()

        # YAML without role key
        (roles_dir / "no_role.yaml").write_text("name: test\ndescription: test")

        registry = RoleRegistry(roles_dir=roles_dir)
        # Should not crash, role should not be loaded
        assert "no_role" not in registry.roles

    @pytest.mark.unit
    def test_orchestrator_role_structure(self, registry):
        """Test orchestrator role has specific structure"""
        role = registry.get_role("orchestrator")

        assert role is not None
        assert "task_analyzer" in role.get("tools", [])
        assert role.get("spawn_conditions") == []  # Orchestrator doesn't auto-spawn

    @pytest.mark.unit
    def test_coder_spawn_conditions(self, registry):
        """Test coder role spawn conditions"""
        role = registry.get_role("coder")
        conditions = role.get("spawn_conditions", [])

        assert "code" in conditions
        assert "implement" in conditions
        assert "function" in conditions


class TestGlobalRegistry:
    """Tests for global registry singleton"""

    @pytest.mark.unit
    def test_get_registry_singleton(self):
        """Test get_registry returns singleton"""
        from core.agents.registry import get_registry

        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    @pytest.mark.unit
    def test_get_registry_returns_role_registry(self):
        """Test get_registry returns RoleRegistry instance"""
        from core.agents.registry import RoleRegistry, get_registry

        registry = get_registry()

        assert isinstance(registry, RoleRegistry)
