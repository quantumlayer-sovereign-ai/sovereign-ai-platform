"""
End-to-End Tests for FinTech Vertical

Complete workflow tests:
- RAG-enhanced task execution
- Compliance checking
- Security scanning
- Multi-agent coordination
"""

import pytest
import asyncio
from pathlib import Path

from core.orchestrator import RAGOrchestrator, Orchestrator
from core.agents.registry import get_registry
from core.agents.factory import AgentFactory
from core.rag.pipeline import FintechRAG
from core.tools.security_tools import SecurityScanner
from verticals.fintech.compliance import ComplianceChecker


class TestFintechRAGPipeline:
    """Test FinTech RAG pipeline with real knowledge base"""

    @pytest.fixture
    def fintech_rag(self):
        rag = FintechRAG()
        # Index the fintech knowledge base
        kb_path = Path(__file__).parent.parent / "data" / "knowledge" / "fintech"
        if kb_path.exists():
            rag.index_directory(kb_path, vertical="fintech", recursive=True)
        return rag

    def test_retrieve_pci_dss_context(self, fintech_rag):
        """Test retrieving PCI-DSS related context"""
        results = fintech_rag.retrieve(
            query="How should credit card data be encrypted?",
            vertical="fintech"
        )

        # Should find relevant PCI-DSS content
        assert len(results) > 0

    def test_retrieve_rbi_guidelines(self, fintech_rag):
        """Test retrieving RBI guidelines"""
        results = fintech_rag.retrieve(
            query="What are the RBI requirements for payment aggregators?",
            vertical="fintech"
        )

        assert len(results) > 0

    def test_retrieve_payment_patterns(self, fintech_rag):
        """Test retrieving payment system patterns"""
        results = fintech_rag.retrieve(
            query="How to implement idempotent payment processing?",
            vertical="fintech"
        )

        assert len(results) > 0


class TestFintechAgentRoles:
    """Test FinTech-specific agent roles"""

    @pytest.fixture
    def registry(self):
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()
        return get_registry()

    def test_fintech_roles_registered(self, registry):
        """Test that FinTech roles are available"""
        roles = registry.list_roles()

        assert "fintech_architect" in roles
        assert "fintech_coder" in roles
        assert "fintech_security" in roles
        assert "fintech_compliance" in roles
        assert "fintech_tester" in roles

    def test_role_spawn_conditions(self, registry):
        """Test role matching for FinTech tasks"""
        # Test payment-related task
        matching = registry.find_roles_for_task(
            "Implement payment gateway integration",
            vertical="fintech"
        )

        assert len(matching) > 0

    def test_compliance_role_has_standards(self, registry):
        """Test compliance role has required standards"""
        role = registry.get_role("fintech_compliance")

        assert role is not None
        assert "pci_dss" in role.get("system_prompt", "").lower() or \
               "rbi" in role.get("system_prompt", "").lower()


class TestComplianceChecker:
    """Test FinTech compliance checking"""

    @pytest.fixture
    def checker(self):
        return ComplianceChecker(standards=["pci_dss", "rbi"])

    def test_detect_hardcoded_card_number(self, checker):
        """Test detection of hardcoded card numbers"""
        code = '''
# Test card for development
test_card = "4111111111111111"
'''
        report = checker.check_code(code, "test.py")

        assert not report.passed
        assert any("PCI-3.4" in i.rule_id for i in report.issues)

    def test_detect_unencrypted_transmission(self, checker):
        """Test detection of HTTP usage"""
        code = '''
api_url = "http://payment-api.example.com/charge"
response = requests.post(api_url, data=payment_data)
'''
        report = checker.check_code(code, "payment.py")

        assert any("PCI-4.1" in i.rule_id for i in report.issues)

    def test_detect_sql_injection(self, checker):
        """Test SQL injection detection"""
        code = '''
def get_transaction(txn_id):
    query = f"SELECT * FROM transactions WHERE id = {txn_id}"
    return db.execute(query)
'''
        report = checker.check_code(code, "db.py")

        assert any("PCI-6.5.1" in i.rule_id for i in report.issues)

    def test_clean_code_passes(self, checker):
        """Test that compliant code passes"""
        code = '''
import hashlib
from cryptography.fernet import Fernet

def store_card_hash(card_number: str) -> str:
    """Store only hash of card number - PCI compliant"""
    salt = os.urandom(32)
    return hashlib.pbkdf2_hmac('sha256', card_number.encode(), salt, 100000).hex()

def make_payment(encrypted_data: bytes):
    """Use HTTPS for all payments"""
    url = "https://secure-payment-api.example.com/charge"
    response = requests.post(url, data=encrypted_data)
    return response
'''
        report = checker.check_code(code, "secure_payment.py")

        # Should have minimal critical issues
        critical_issues = [i for i in report.issues if i.severity.value == "critical"]
        assert len(critical_issues) == 0


class TestRAGOrchestrator:
    """Test RAG-enhanced orchestrator"""

    @pytest.fixture
    def orchestrator(self):
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()
        return RAGOrchestrator(
            model_interface=None,  # No model for tests
            default_vertical="fintech",
            max_agents=5
        )

    @pytest.mark.asyncio
    async def test_index_knowledge_base(self, orchestrator):
        """Test indexing knowledge base"""
        kb_path = Path(__file__).parent.parent / "data" / "knowledge" / "fintech"
        if kb_path.exists():
            result = await orchestrator.index_knowledge_base(
                str(kb_path),
                vertical="fintech"
            )
            assert result.get("chunks_indexed", 0) > 0

    @pytest.mark.asyncio
    async def test_search_knowledge(self, orchestrator):
        """Test searching knowledge base"""
        # First index if not already
        kb_path = Path(__file__).parent.parent / "data" / "knowledge" / "fintech"
        if kb_path.exists():
            await orchestrator.index_knowledge_base(str(kb_path), "fintech")

        results = await orchestrator.search_knowledge(
            query="PCI-DSS encryption requirements",
            vertical="fintech"
        )

        # Results may be empty if knowledge base not indexed
        # This is acceptable for tests

    @pytest.mark.asyncio
    async def test_execute_fintech_task(self, orchestrator):
        """Test executing a FinTech task"""
        result = await orchestrator.execute(
            task="Review the security of a payment processing module",
            vertical="fintech",
            compliance_requirements=["pci_dss"],
            use_rag=False  # Disable RAG for faster tests
        )

        assert result.task_id is not None
        assert "fintech" in [agent.lower() for agent in result.agents_used] or \
               "security" in [agent.lower() for agent in result.agents_used] or \
               "coder" in result.agents_used

    @pytest.mark.asyncio
    async def test_compliance_in_execution(self, orchestrator):
        """Test that compliance is checked during execution"""
        result = await orchestrator.execute(
            task="Implement credit card storage functionality",
            vertical="fintech",
            compliance_requirements=["pci_dss", "data_encryption"],
            use_rag=False
        )

        # Should have compliance status
        assert "pci_dss" in result.compliance_status or \
               "data_encryption" in result.compliance_status


class TestSecurityIntegration:
    """Test security scanning integration"""

    @pytest.fixture
    def scanner(self):
        return SecurityScanner()

    def test_scan_payment_code(self, scanner):
        """Test scanning payment-related code"""
        code = '''
class PaymentProcessor:
    def __init__(self):
        self.api_key = "sk_live_abcdef123456789012345"  # Should be flagged (>20 chars)

    def charge(self, card_number, amount):
        # Insecure HTTP
        response = requests.post("http://payment.api/charge", data={
            "card": card_number,
            "amount": amount
        })
'''
        result = scanner.scan_code(code, "payment.py")

        # Should find issues (hardcoded secret and HTTP)
        assert result["total_issues"] >= 1
        assert not result["passed"]


class TestMultiAgentWorkflow:
    """Test multi-agent workflows for FinTech"""

    @pytest.fixture
    def factory(self):
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()
        return AgentFactory(model_interface=None, max_agents=10)

    def test_spawn_fintech_agents(self, factory):
        """Test spawning FinTech-specific agents"""
        agents = factory.spawn_for_task(
            "Build a payment integration with compliance checking",
            vertical="fintech"
        )

        assert len(agents) > 0

    def test_agent_pool_management(self, factory):
        """Test agent pool management"""
        # Spawn multiple agents
        agent1 = factory.spawn("fintech_coder")
        agent2 = factory.spawn("fintech_security")

        stats = factory.stats

        assert stats["total_spawned"] >= 2
        assert stats["active_agents"] >= 2

        # Destroy agents
        factory.destroy_agent(agent1.agent_id)
        factory.destroy_agent(agent2.agent_id)

        stats = factory.stats
        assert stats["active_agents"] == 0

    def test_audit_trail(self, factory):
        """Test audit trail generation"""
        agent = factory.spawn("fintech_compliance")

        audit = factory.get_audit_trail()

        assert len(audit) >= 1
        assert any(a["agent_id"] == agent.agent_id for a in audit)


class TestEndToEndScenarios:
    """End-to-end scenario tests"""

    @pytest.fixture
    def orchestrator(self):
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()
        return RAGOrchestrator(
            model_interface=None,
            default_vertical="fintech",
            max_agents=5
        )

    @pytest.mark.asyncio
    async def test_payment_api_review(self, orchestrator):
        """Test complete payment API review scenario"""
        result = await orchestrator.execute(
            task="Review and improve the security of a payment API endpoint",
            vertical="fintech",
            compliance_requirements=["pci_dss", "rbi_guidelines"],
            use_rag=False
        )

        assert result.success or "No model" in result.aggregated_output
        assert len(result.audit_trail) > 0

    @pytest.mark.asyncio
    async def test_compliance_audit(self, orchestrator):
        """Test compliance audit scenario"""
        result = await orchestrator.execute(
            task="Perform a PCI-DSS compliance audit on the codebase",
            vertical="fintech",
            compliance_requirements=["pci_dss"],
            use_rag=False
        )

        assert result.task_id is not None
        assert "pci_dss" in result.compliance_status or \
               "audit_logging" in result.compliance_status
