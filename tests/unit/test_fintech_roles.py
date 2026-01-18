"""
Unit Tests for FinTech Roles

Tests:
- Role definitions
- Role registration
- Role structure validation
- Compliance awareness
"""

import pytest


class TestFintechRolesUnit:
    """Unit tests for FinTech role definitions"""

    @pytest.fixture
    def fintech_roles(self):
        """Get FinTech roles dict"""
        from verticals.fintech.roles import FINTECH_ROLES
        return FINTECH_ROLES

    @pytest.mark.unit
    def test_all_fintech_roles_defined(self, fintech_roles):
        """Test all expected FinTech roles are defined"""
        expected_roles = [
            "fintech_architect",
            "fintech_coder",
            "fintech_security",
            "fintech_compliance",
            "fintech_tester"
        ]

        for role in expected_roles:
            assert role in fintech_roles, f"Missing FinTech role: {role}"

    @pytest.mark.unit
    def test_fintech_architect_structure(self, fintech_roles):
        """Test fintech_architect role structure"""
        role = fintech_roles["fintech_architect"]

        assert role["name"] == "fintech_architect"
        assert "system_prompt" in role
        assert "tools" in role
        assert "spawn_conditions" in role
        assert role["vertical"] == "fintech"
        assert "compliance" in role

    @pytest.mark.unit
    def test_fintech_architect_compliance(self, fintech_roles):
        """Test fintech_architect has compliance requirements"""
        role = fintech_roles["fintech_architect"]
        compliance = role["compliance"]

        assert "pci_dss" in compliance
        assert "rbi" in compliance

    @pytest.mark.unit
    def test_fintech_architect_prompt_content(self, fintech_roles):
        """Test fintech_architect prompt contains key topics"""
        prompt = fintech_roles["fintech_architect"]["system_prompt"]

        assert "payment" in prompt.lower()
        assert "pci-dss" in prompt.lower()
        assert "rbi" in prompt.lower()
        assert "encryption" in prompt.lower()

    @pytest.mark.unit
    def test_fintech_coder_structure(self, fintech_roles):
        """Test fintech_coder role structure"""
        role = fintech_roles["fintech_coder"]

        assert role["name"] == "fintech_coder"
        assert role["vertical"] == "fintech"
        assert "security_scanner" in role["tools"]

    @pytest.mark.unit
    def test_fintech_coder_security_rules(self, fintech_roles):
        """Test fintech_coder prompt contains security rules"""
        prompt = fintech_roles["fintech_coder"]["system_prompt"]

        assert "never log sensitive data" in prompt.lower()
        assert "parameterized queries" in prompt.lower()
        assert "tls" in prompt.lower()
        assert "never hardcode" in prompt.lower()

    @pytest.mark.unit
    def test_fintech_coder_spawn_conditions(self, fintech_roles):
        """Test fintech_coder spawn conditions"""
        conditions = fintech_roles["fintech_coder"]["spawn_conditions"]

        assert "payment" in conditions
        assert "upi" in conditions
        assert "transaction" in conditions

    @pytest.mark.unit
    def test_fintech_security_structure(self, fintech_roles):
        """Test fintech_security role structure"""
        role = fintech_roles["fintech_security"]

        assert role["name"] == "fintech_security"
        assert "security_scanner" in role["tools"]
        assert "vulnerability_db" in role["tools"]

    @pytest.mark.unit
    def test_fintech_security_pci_requirements(self, fintech_roles):
        """Test fintech_security covers PCI-DSS requirements"""
        prompt = fintech_roles["fintech_security"]["system_prompt"]

        # Should mention key PCI requirements
        assert "requirement 1" in prompt.lower()
        assert "requirement 3" in prompt.lower()
        assert "requirement 6" in prompt.lower()

    @pytest.mark.unit
    def test_fintech_compliance_structure(self, fintech_roles):
        """Test fintech_compliance role structure"""
        role = fintech_roles["fintech_compliance"]

        assert role["name"] == "fintech_compliance"
        assert "compliance_checker" in role["tools"]
        assert "pci_dss" in role["compliance"]
        assert "rbi" in role["compliance"]
        assert "dpdp" in role["compliance"]

    @pytest.mark.unit
    def test_fintech_compliance_rbi_guidelines(self, fintech_roles):
        """Test fintech_compliance covers RBI guidelines"""
        prompt = fintech_roles["fintech_compliance"]["system_prompt"]

        assert "rbi" in prompt.lower()
        assert "payment aggregator" in prompt.lower()
        assert "data localization" in prompt.lower()

    @pytest.mark.unit
    def test_fintech_compliance_dpdp(self, fintech_roles):
        """Test fintech_compliance covers DPDP Act"""
        prompt = fintech_roles["fintech_compliance"]["system_prompt"]

        assert "dpdp" in prompt.lower()
        assert "consent" in prompt.lower()

    @pytest.mark.unit
    def test_fintech_tester_structure(self, fintech_roles):
        """Test fintech_tester role structure"""
        role = fintech_roles["fintech_tester"]

        assert role["name"] == "fintech_tester"
        assert "test_runner" in role["tools"]
        assert "api_tester" in role["tools"]

    @pytest.mark.unit
    def test_fintech_tester_test_data(self, fintech_roles):
        """Test fintech_tester mentions test data patterns"""
        prompt = fintech_roles["fintech_tester"]["system_prompt"]

        # Should mention test card and test UPI
        assert "4111" in prompt  # Test card number
        assert "success@upi" in prompt or "test" in prompt.lower()

    @pytest.mark.unit
    def test_fintech_tester_safety_warnings(self, fintech_roles):
        """Test fintech_tester has safety warnings"""
        prompt = fintech_roles["fintech_tester"]["system_prompt"]

        assert "never use real card" in prompt.lower()
        assert "never test on production" in prompt.lower()

    @pytest.mark.unit
    def test_all_roles_have_vertical(self, fintech_roles):
        """Test all FinTech roles have vertical set"""
        for role_name, role in fintech_roles.items():
            assert role.get("vertical") == "fintech", f"{role_name} missing vertical"

    @pytest.mark.unit
    def test_all_roles_have_name(self, fintech_roles):
        """Test all roles have name matching key"""
        for role_name, role in fintech_roles.items():
            assert role["name"] == role_name

    @pytest.mark.unit
    def test_all_roles_have_system_prompt(self, fintech_roles):
        """Test all roles have system prompts"""
        for role_name, role in fintech_roles.items():
            assert "system_prompt" in role
            assert len(role["system_prompt"]) > 100  # Should be substantial

    @pytest.mark.unit
    def test_all_roles_have_tools(self, fintech_roles):
        """Test all roles have tools defined"""
        for role_name, role in fintech_roles.items():
            assert "tools" in role
            assert isinstance(role["tools"], list)
            assert len(role["tools"]) > 0

    @pytest.mark.unit
    def test_all_roles_have_spawn_conditions(self, fintech_roles):
        """Test all roles have spawn conditions"""
        for role_name, role in fintech_roles.items():
            assert "spawn_conditions" in role
            assert isinstance(role["spawn_conditions"], list)


class TestRegisterFintechRoles:
    """Tests for register_fintech_roles function"""

    @pytest.mark.unit
    def test_register_fintech_roles(self):
        """Test registering FinTech roles with registry"""
        from verticals.fintech.roles import register_fintech_roles

        registered = register_fintech_roles()

        assert "fintech_architect" in registered
        assert "fintech_coder" in registered
        assert "fintech_security" in registered
        assert "fintech_compliance" in registered
        assert "fintech_tester" in registered

    @pytest.mark.unit
    def test_registered_roles_in_registry(self):
        """Test registered roles are accessible from registry"""
        from core.agents.registry import get_registry
        from verticals.fintech.roles import register_fintech_roles

        register_fintech_roles()
        registry = get_registry()

        assert registry.get_role("fintech_coder") is not None
        assert registry.get_role("fintech_security") is not None

    @pytest.mark.unit
    def test_registered_roles_have_compliance(self):
        """Test registered roles have compliance info"""
        from core.agents.registry import get_registry
        from verticals.fintech.roles import register_fintech_roles

        register_fintech_roles()
        registry = get_registry()

        role = registry.get_role("fintech_compliance")
        assert "pci_dss" in role.get("compliance", [])


class TestFintechVerticalInit:
    """Tests for verticals/fintech/__init__.py"""

    @pytest.mark.unit
    def test_fintech_module_exports(self):
        """Test fintech module exports expected items"""
        from verticals.fintech import (
            FINTECH_ROLES,
            ComplianceChecker,
            register_fintech_roles,
        )

        assert FINTECH_ROLES is not None
        assert ComplianceChecker is not None
        assert callable(register_fintech_roles)
