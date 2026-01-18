"""
Unit Tests for RAG Orchestrator

Tests:
- Initialization
- Context retrieval
- Prompt enhancement
- Security scanning
- RAG statistics
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import requires_chromadb


class TestRAGOrchestratorUnit:
    """Unit tests for RAGOrchestrator class"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register FinTech roles before tests"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create RAGOrchestrator instance"""
        from core.orchestrator import RAGOrchestrator

        db_path = tmp_path / "vectordb"
        db_path.mkdir()

        return RAGOrchestrator(
            model_interface=None,
            max_agents=5,
            default_vertical="fintech",
            rag_persist_dir=str(db_path)
        )

    @pytest.mark.unit
    def test_orchestrator_initialization(self, orchestrator):
        """Test RAGOrchestrator initialization"""
        assert orchestrator is not None
        assert orchestrator.default_vertical == "fintech"
        assert orchestrator.rag is not None
        assert orchestrator.security_scanner is not None

    @pytest.mark.unit
    def test_orchestrator_has_rag_pipeline(self, orchestrator):
        """Test orchestrator has RAG pipeline"""
        from core.rag.pipeline import RAGPipeline

        assert isinstance(orchestrator.rag, RAGPipeline)

    @pytest.mark.unit
    def test_orchestrator_has_security_scanner(self, orchestrator):
        """Test orchestrator has security scanner"""
        from core.tools.security_tools import SecurityScanner

        assert isinstance(orchestrator.security_scanner, SecurityScanner)

    @pytest.mark.unit
    def test_vertical_rags_empty_initially(self, orchestrator):
        """Test vertical RAGs dict is empty initially"""
        assert orchestrator.vertical_rags == {}

    @pytest.mark.unit
    def test_get_vertical_rag_fintech(self, orchestrator):
        """Test getting FinTech-specific RAG"""
        from core.rag.pipeline import FintechRAG

        rag = orchestrator.get_vertical_rag("fintech")

        assert rag is not None
        assert isinstance(rag, FintechRAG)
        assert "fintech" in orchestrator.vertical_rags

    @pytest.mark.unit
    def test_get_vertical_rag_other(self, orchestrator):
        """Test getting non-fintech RAG returns base RAG"""
        rag = orchestrator.get_vertical_rag("healthcare")

        assert rag is not None
        # Should return the base RAG for non-fintech verticals
        assert rag == orchestrator.rag

    @pytest.mark.unit
    def test_get_vertical_rag_caching(self, orchestrator):
        """Test vertical RAG is cached"""
        rag1 = orchestrator.get_vertical_rag("fintech")
        rag2 = orchestrator.get_vertical_rag("fintech")

        assert rag1 is rag2

    @pytest.mark.unit
    def test_enhance_prompt(self, orchestrator):
        """Test prompt enhancement with RAG context"""
        from core.orchestrator.rag_orchestrator import RAGContext

        original_prompt = "You are a helpful assistant."
        context = RAGContext(
            documents=[{"content": "PCI-DSS requires encryption"}],
            sources=["pci_guide.md"],
            relevance_scores=[0.95],
            context_text="PCI-DSS requires encryption of cardholder data.",
            vertical="fintech"
        )

        enhanced = orchestrator._enhance_prompt(original_prompt, context, "fintech")

        assert original_prompt in enhanced
        assert "Knowledge Base Context" in enhanced
        assert "PCI-DSS" in enhanced
        assert "pci_guide.md" in enhanced

    @pytest.mark.unit
    def test_enhance_prompt_includes_sources(self, orchestrator):
        """Test enhanced prompt includes source citations"""
        from core.orchestrator.rag_orchestrator import RAGContext

        context = RAGContext(
            documents=[],
            sources=["source1.md", "source2.md", "source3.md"],
            relevance_scores=[0.9, 0.85, 0.8],
            context_text="Some context",
            vertical="fintech"
        )

        enhanced = orchestrator._enhance_prompt("Base prompt", context, "fintech")

        assert "source1.md" in enhanced
        assert "source2.md" in enhanced

    @pytest.mark.unit
    def test_get_rag_stats(self, orchestrator):
        """Test getting RAG statistics"""
        stats = orchestrator.get_rag_stats()

        assert "base_rag" in stats
        assert "vertical_rags" in stats
        assert isinstance(stats["vertical_rags"], dict)

    @pytest.mark.unit
    def test_get_rag_stats_with_vertical(self, orchestrator):
        """Test RAG stats include vertical RAGs"""
        # Initialize a vertical RAG
        orchestrator.get_vertical_rag("fintech")

        stats = orchestrator.get_rag_stats()

        assert "fintech" in stats["vertical_rags"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_basic(self, orchestrator):
        """Test basic task execution"""
        result = await orchestrator.execute(
            task="Write a hello world function",
            vertical="fintech",
            use_rag=False
        )

        assert result.task_id is not None
        assert result.success is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_without_rag(self, orchestrator):
        """Test execution with RAG disabled"""
        result = await orchestrator.execute(
            task="Simple task",
            vertical="fintech",
            use_rag=False
        )

        assert result.success is True
        # RAG sources should not be in audit trail when disabled
        rag_sources = [a for a in result.audit_trail if a.get("type") == "rag_sources"]
        assert len(rag_sources) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_compliance(self, orchestrator):
        """Test execution with compliance requirements"""
        result = await orchestrator.execute(
            task="Store payment data",
            vertical="fintech",
            compliance_requirements=["pci_dss"],
            use_rag=False
        )

        assert "pci_dss" in result.compliance_status

    @requires_chromadb
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_index_knowledge_base(self, orchestrator, tmp_path):
        """Test indexing knowledge base"""
        # Create test documents
        kb_path = tmp_path / "kb"
        kb_path.mkdir()
        (kb_path / "test.md").write_text("# Test Document\n\nSome content here.")

        result = await orchestrator.index_knowledge_base(
            str(kb_path),
            vertical="fintech"
        )

        assert result.get("chunks_indexed", 0) > 0

    @requires_chromadb
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_knowledge(self, orchestrator, tmp_path):
        """Test searching knowledge base"""
        # Create and index test documents
        kb_path = tmp_path / "kb"
        kb_path.mkdir()
        (kb_path / "pci.md").write_text("PCI-DSS requires encryption of card data.")

        await orchestrator.index_knowledge_base(str(kb_path), "fintech")

        results = await orchestrator.search_knowledge(
            query="encryption requirements",
            vertical="fintech"
        )

        assert isinstance(results, list)


class TestRAGContextUnit:
    """Unit tests for RAGContext dataclass"""

    @pytest.mark.unit
    def test_rag_context_creation(self):
        """Test RAGContext creation"""
        from core.orchestrator.rag_orchestrator import RAGContext

        context = RAGContext(
            documents=[{"content": "test"}],
            sources=["source.md"],
            relevance_scores=[0.9],
            context_text="Test context",
            vertical="fintech"
        )

        assert len(context.documents) == 1
        assert context.vertical == "fintech"
        assert context.sources == ["source.md"]


class TestSecurityScanningUnit:
    """Unit tests for security scanning in RAGOrchestrator"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register roles"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator"""
        from core.orchestrator import RAGOrchestrator

        return RAGOrchestrator(
            model_interface=None,
            max_agents=5,
            default_vertical="fintech",
            rag_persist_dir=str(tmp_path)
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scan_results_empty(self, orchestrator):
        """Test scanning empty results"""
        results = []
        scan = await orchestrator._scan_results_for_security(results)

        assert scan["scanned"] is True
        assert scan["issues"] == []
        assert scan["passed"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scan_results_clean_code(self, orchestrator):
        """Test scanning clean code in results"""
        results = [{
            "response": '''Here's clean code:
```python
def add(a, b):
    return a + b
```
'''
        }]

        scan = await orchestrator._scan_results_for_security(results)

        assert scan["scanned"] is True
        assert scan["passed"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scan_results_vulnerable_code(self, orchestrator):
        """Test scanning vulnerable code in results"""
        results = [{
            "response": '''Here's code with issues:
```python
password = "supersecretpassword123"
url = "http://api.example.com"
```
'''
        }]

        scan = await orchestrator._scan_results_for_security(results)

        assert scan["scanned"] is True
        assert len(scan["issues"]) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scan_results_no_code_blocks(self, orchestrator):
        """Test scanning results without code blocks"""
        results = [{
            "response": "This is just text without any code blocks."
        }]

        scan = await orchestrator._scan_results_for_security(results)

        assert scan["scanned"] is True
        assert scan["issues"] == []


class TestRAGOrchestratorInheritance:
    """Tests for RAGOrchestrator inheritance from Orchestrator"""

    @pytest.fixture(autouse=True)
    def setup_roles(self):
        """Register roles"""
        from verticals.fintech import register_fintech_roles
        register_fintech_roles()

    @pytest.mark.unit
    def test_inherits_from_orchestrator(self, tmp_path):
        """Test RAGOrchestrator inherits from Orchestrator"""
        from core.orchestrator.main import Orchestrator
        from core.orchestrator.rag_orchestrator import RAGOrchestrator

        orch = RAGOrchestrator(rag_persist_dir=str(tmp_path))

        assert isinstance(orch, Orchestrator)

    @pytest.mark.unit
    def test_has_factory(self, tmp_path):
        """Test RAGOrchestrator has agent factory"""
        from core.orchestrator.rag_orchestrator import RAGOrchestrator

        orch = RAGOrchestrator(rag_persist_dir=str(tmp_path))

        assert orch.factory is not None

    @pytest.mark.unit
    def test_has_task_history(self, tmp_path):
        """Test RAGOrchestrator has task history"""
        from core.orchestrator.rag_orchestrator import RAGOrchestrator

        orch = RAGOrchestrator(rag_persist_dir=str(tmp_path))

        assert hasattr(orch, 'task_history')
        assert isinstance(orch.task_history, list)
