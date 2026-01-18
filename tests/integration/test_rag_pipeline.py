"""
Integration Tests for RAG Pipeline

Tests full RAG workflow:
- Document loading → Chunking → Embedding → Storage → Retrieval
"""


import pytest

from tests.conftest import requires_chromadb, requires_rag, requires_sentence_transformers


@requires_rag
@pytest.mark.integration
class TestRAGPipelineIntegration:
    """Integration tests for complete RAG pipeline"""

    @pytest.fixture
    def temp_knowledge_base(self, tmp_path):
        """Create temporary knowledge base with test documents"""
        kb_path = tmp_path / "knowledge"
        kb_path.mkdir()

        # Create test documents
        (kb_path / "pci_dss.md").write_text("""
# PCI-DSS Requirements

## Requirement 3.4
Render PAN unreadable anywhere it is stored using:
- One-way hashes based on strong cryptography
- Truncation
- Index tokens and pads
- Strong cryptography with associated key-management

## Requirement 4.1
Use strong cryptography and security protocols to safeguard sensitive
cardholder data during transmission over open, public networks.
""")

        (kb_path / "secure_coding.md").write_text("""
# Secure Coding Patterns

## Password Hashing
Always use bcrypt or Argon2 for password hashing.
Never use MD5 or SHA1 for passwords.

## SQL Injection Prevention
Use parameterized queries or prepared statements.
Never concatenate user input into SQL queries.

## API Security
- Always use HTTPS
- Implement rate limiting
- Validate all inputs
""")

        (kb_path / "payment_patterns.py").write_text("""
# Payment Processing Patterns

def process_payment(token: str, amount: float):
    '''
    Process payment using tokenized card.
    Never store actual card numbers.
    '''
    pass

def idempotent_transaction(transaction_id: str):
    '''
    Implement idempotency to prevent duplicate charges.
    '''
    pass
""")

        return kb_path

    @pytest.fixture
    def temp_vectordb(self, tmp_path):
        """Create temporary vector database directory"""
        db_path = tmp_path / "vectordb"
        db_path.mkdir()
        return db_path

    @pytest.mark.integration
    def test_full_pipeline_index_and_search(self, temp_knowledge_base, temp_vectordb):
        """Test complete indexing and search flow"""
        from core.rag.pipeline import RAGPipeline

        # Initialize pipeline
        pipeline = RAGPipeline(
            persist_directory=str(temp_vectordb),
            embedding_model="minilm"
        )

        # Index documents
        result = pipeline.index_directory(
            directory=temp_knowledge_base,
            vertical="fintech",
            recursive=True
        )

        assert result["chunks_indexed"] > 0

        # Search
        results = pipeline.retrieve(
            query="How to hash passwords securely?",
            vertical="fintech",
            n_results=3
        )

        assert len(results) > 0
        # Should find bcrypt/Argon2 reference
        all_content = " ".join(r["content"].lower() for r in results)
        assert "bcrypt" in all_content or "argon2" in all_content or "hash" in all_content

    @pytest.mark.integration
    def test_search_pci_requirements(self, temp_knowledge_base, temp_vectordb):
        """Test searching for PCI-DSS requirements"""
        from core.rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(persist_directory=str(temp_vectordb))
        pipeline.index_directory(temp_knowledge_base, vertical="fintech")

        results = pipeline.retrieve(
            query="How should credit card data be stored?",
            vertical="fintech"
        )

        assert len(results) > 0
        # Should find PCI reference
        all_content = " ".join(r["content"].lower() for r in results)
        assert "pci" in all_content or "pan" in all_content or "encrypt" in all_content

    @pytest.mark.integration
    def test_search_sql_injection(self, temp_knowledge_base, temp_vectordb):
        """Test searching for SQL injection prevention"""
        from core.rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(persist_directory=str(temp_vectordb))
        pipeline.index_directory(temp_knowledge_base, vertical="fintech")

        results = pipeline.retrieve(
            query="How to prevent SQL injection?",
            vertical="fintech"
        )

        assert len(results) > 0
        all_content = " ".join(r["content"].lower() for r in results)
        assert "sql" in all_content or "parameterized" in all_content

    @pytest.mark.integration
    def test_retrieve_with_context(self, temp_knowledge_base, temp_vectordb):
        """Test retrieval with formatted context"""
        from core.rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(persist_directory=str(temp_vectordb))
        pipeline.index_directory(temp_knowledge_base, vertical="fintech")

        result = pipeline.retrieve_with_context(
            query="Payment security best practices",
            vertical="fintech",
            n_results=3
        )

        assert result["found"] is True
        assert "context" in result
        assert "sources" in result
        assert len(result["context"]) > 0

    @pytest.mark.integration
    def test_metadata_filtering(self, temp_knowledge_base, temp_vectordb):
        """Test search with metadata filtering"""
        from core.rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(persist_directory=str(temp_vectordb))
        pipeline.index_directory(temp_knowledge_base, vertical="fintech")

        # Search with file type filter (if supported)
        results = pipeline.retrieve(
            query="payment processing",
            vertical="fintech",
            n_results=5
        )

        assert len(results) > 0

    @pytest.mark.integration
    def test_pipeline_stats(self, temp_knowledge_base, temp_vectordb):
        """Test pipeline statistics"""
        from core.rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(persist_directory=str(temp_vectordb))
        pipeline.index_directory(temp_knowledge_base, vertical="fintech")

        stats = pipeline.get_stats()

        # Stats is keyed by vertical
        assert "fintech" in stats
        assert "count" in stats["fintech"]
        assert stats["fintech"]["count"] > 0

    @pytest.mark.integration
    def test_incremental_indexing(self, temp_knowledge_base, temp_vectordb):
        """Test adding more documents incrementally"""
        from core.rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(persist_directory=str(temp_vectordb))

        # Initial indexing
        result1 = pipeline.index_directory(temp_knowledge_base, vertical="fintech")
        initial_count = result1["chunks_indexed"]

        # Add another document
        (temp_knowledge_base / "new_doc.md").write_text("""
# New Security Guidelines

## Token Management
Always rotate API tokens regularly.
Implement token expiration.
""")

        # Index again
        result2 = pipeline.index_directory(temp_knowledge_base, vertical="fintech")

        # Should have more documents now
        assert result2["chunks_indexed"] >= initial_count


@requires_rag
@pytest.mark.integration
class TestFintechRAGIntegration:
    """Integration tests for FinTech-specific RAG"""

    @pytest.fixture
    def fintech_rag(self, tmp_path):
        """Create FinTech RAG with test data"""
        from core.rag.pipeline import FintechRAG

        kb_path = tmp_path / "fintech_kb"
        kb_path.mkdir()

        # Create fintech-specific documents
        (kb_path / "rbi_guidelines.md").write_text("""
# RBI Payment Aggregator Guidelines

## Tokenization Requirements
All PA/PGs must implement card-on-file tokenization.
No actual card data should be stored after 2022.

## Escrow Requirements
Payment aggregators must maintain escrow accounts.
Settlement within T+1 business days.

## KYC Requirements
- Minimum KYC for transactions up to Rs. 10,000
- Full KYC required for higher amounts
""")

        db_path = tmp_path / "vectordb"
        db_path.mkdir()

        rag = FintechRAG(persist_directory=str(db_path))
        rag.index_directory(kb_path, vertical="fintech")

        return rag

    @pytest.mark.integration
    def test_retrieve_compliance(self, fintech_rag):
        """Test compliance-specific retrieval"""
        results = fintech_rag.retrieve_compliance(
            query="What are the tokenization requirements?"
        )

        assert len(results) > 0

    @pytest.mark.integration
    def test_rbi_guidelines_search(self, fintech_rag):
        """Test RBI guidelines search"""
        results = fintech_rag.retrieve(
            query="RBI payment aggregator escrow requirements",
            vertical="fintech"
        )

        assert len(results) > 0
        all_content = " ".join(r["content"].lower() for r in results)
        assert "escrow" in all_content or "rbi" in all_content


@requires_sentence_transformers
@pytest.mark.integration
class TestEmbeddingIntegration:
    """Integration tests for embedding model"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_embedding_model(self):
        """Test with real sentence-transformers model"""
        from core.rag.embeddings import EmbeddingModel

        model = EmbeddingModel(model_name="minilm")

        # Test single embedding
        embedding = model.embed_query("Test query")

        assert len(embedding) == 384

    @pytest.mark.integration
    @pytest.mark.slow
    def test_batch_embedding(self):
        """Test batch embedding"""
        from core.rag.embeddings import EmbeddingModel

        model = EmbeddingModel(model_name="minilm")

        texts = [
            "First document about payments",
            "Second document about security",
            "Third document about compliance"
        ]

        embeddings = model.embed(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 384

    @pytest.mark.integration
    @pytest.mark.slow
    def test_embedding_similarity(self):
        """Test that similar texts have similar embeddings"""
        import numpy as np

        from core.rag.embeddings import EmbeddingModel

        model = EmbeddingModel(model_name="minilm")

        # Similar texts
        text1 = "How to securely store passwords"
        text2 = "Password storage best practices"
        # Different text
        text3 = "The weather is nice today"

        emb1 = np.array(model.embed_query(text1))
        emb2 = np.array(model.embed_query(text2))
        emb3 = np.array(model.embed_query(text3))

        # Cosine similarity
        def cosine_sim(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim_12 = cosine_sim(emb1, emb2)
        sim_13 = cosine_sim(emb1, emb3)

        # Similar texts should have higher similarity
        assert sim_12 > sim_13
