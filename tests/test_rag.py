"""
Tests for RAG Pipeline

Tests:
- Document loading and chunking
- Embedding generation
- Vector store operations
- Retrieval accuracy
"""

import pytest
import tempfile
from pathlib import Path

from core.rag.loader import DocumentLoader, Document, Chunk
from core.rag.embeddings import EmbeddingModel
from core.rag.vectorstore import VectorStore
from core.rag.pipeline import RAGPipeline, FintechRAG


class TestDocumentLoader:
    """Test document loading and chunking"""

    def test_load_text_file(self, tmp_path):
        """Test loading a text file"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document.\n\nWith multiple paragraphs.")

        loader = DocumentLoader()
        doc = loader.load_file(test_file)

        assert doc is not None
        assert "test document" in doc.content
        assert doc.metadata["file_type"] == "text"

    def test_load_python_file(self, tmp_path):
        """Test loading a Python file"""
        test_file = tmp_path / "test.py"
        test_file.write_text('def hello():\n    return "Hello, World!"')

        loader = DocumentLoader()
        doc = loader.load_file(test_file)

        assert doc is not None
        assert "def hello" in doc.content
        assert doc.metadata["file_type"] == "python"

    def test_chunk_document(self):
        """Test document chunking"""
        content = "First paragraph.\n\n" * 50  # Create long content
        doc = Document(content=content)

        loader = DocumentLoader(chunk_size=200, chunk_overlap=50)
        chunks = loader.chunk_document(doc)

        assert len(chunks) > 1
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(len(c.content) <= 250 for c in chunks)  # With some tolerance

    def test_load_directory(self, tmp_path):
        """Test loading all files from directory"""
        # Create test files
        (tmp_path / "file1.txt").write_text("Content 1")
        (tmp_path / "file2.py").write_text("# Python code")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("Content 3")

        loader = DocumentLoader()
        docs = loader.load_directory(tmp_path, recursive=True)

        assert len(docs) == 3

    def test_load_and_chunk(self, tmp_path):
        """Test combined load and chunk"""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Heading\n\n" + "Content.\n\n" * 20)

        loader = DocumentLoader(chunk_size=100)
        chunks = loader.load_and_chunk(test_file)

        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)


class TestEmbeddingModel:
    """Test embedding generation"""

    @pytest.fixture
    def embedding_model(self):
        model = EmbeddingModel(model_name="minilm")
        return model

    def test_embed_single(self, embedding_model):
        """Test single text embedding"""
        text = "This is a test sentence."
        embedding = embedding_model.embed_query(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 384  # MiniLM dimension

    def test_embed_multiple(self, embedding_model):
        """Test batch embedding"""
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence."
        ]
        embeddings = embedding_model.embed(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

    def test_similarity(self, embedding_model):
        """Test similarity calculation"""
        e1 = embedding_model.embed_query("payment processing")
        e2 = embedding_model.embed_query("payment transactions")
        e3 = embedding_model.embed_query("weather forecast")

        sim_related = embedding_model.similarity(e1, e2)
        sim_unrelated = embedding_model.similarity(e1, e3)

        assert sim_related > sim_unrelated


class TestVectorStore:
    """Test vector store operations"""

    @pytest.fixture
    def vector_store(self):
        # Use in-memory store for tests
        store = VectorStore(collection_name="test_collection")
        store.connect()
        yield store
        # Cleanup
        try:
            store.delete_collection()
        except:
            pass

    def test_add_and_search(self, vector_store):
        """Test adding chunks and searching"""
        chunks = [
            Chunk(content="PCI-DSS requires encryption of cardholder data",
                  doc_id="doc1", chunk_id="0", metadata={"source": "pci.md"}),
            Chunk(content="Payment gateway integration guide",
                  doc_id="doc2", chunk_id="0", metadata={"source": "gateway.md"}),
            Chunk(content="Weather patterns in tropical regions",
                  doc_id="doc3", chunk_id="0", metadata={"source": "weather.md"}),
        ]

        vector_store.add_chunks(chunks)

        # Search for payment-related
        results = vector_store.search("credit card security", n_results=2)

        assert len(results) == 2
        assert any("PCI-DSS" in r["content"] for r in results)

    def test_metadata_filter(self, vector_store):
        """Test searching with metadata filter"""
        chunks = [
            Chunk(content="Fintech compliance rules",
                  doc_id="doc1", chunk_id="0",
                  metadata={"vertical": "fintech", "source": "rules.md"}),
            Chunk(content="Healthcare compliance rules",
                  doc_id="doc2", chunk_id="0",
                  metadata={"vertical": "healthcare", "source": "hipaa.md"}),
        ]

        vector_store.add_chunks(chunks)

        # Filter by vertical
        results = vector_store.search(
            "compliance",
            n_results=2,
            where={"vertical": "fintech"}
        )

        assert len(results) == 1
        assert "Fintech" in results[0]["content"]

    def test_get_stats(self, vector_store):
        """Test getting collection stats"""
        chunks = [
            Chunk(content="Test content", doc_id="doc1", chunk_id="0",
                  metadata={"source": "test.txt"})  # Non-empty metadata required
        ]
        vector_store.add_chunks(chunks)

        stats = vector_store.get_stats()

        assert stats["collection"] == "test_collection"
        assert stats["count"] == 1


class TestRAGPipeline:
    """Test complete RAG pipeline"""

    @pytest.fixture
    def rag_pipeline(self):
        pipeline = RAGPipeline(chunk_size=500)
        return pipeline

    def test_index_text(self, rag_pipeline):
        """Test indexing text content"""
        text = """
        PCI-DSS Requirement 3: Protect stored cardholder data.

        This requirement covers encryption, masking, and secure storage
        of payment card information.
        """

        result = rag_pipeline.index_text(
            text=text,
            vertical="fintech",
            source="pci_docs"
        )

        assert result["success"]
        assert result["chunks_indexed"] > 0

    def test_retrieve(self, rag_pipeline):
        """Test retrieval after indexing"""
        # Index some content
        rag_pipeline.index_text(
            text="Payment gateway must use TLS 1.2 or higher for secure transmission.",
            vertical="fintech",
            source="security_guide"
        )

        results = rag_pipeline.retrieve(
            query="secure payment transmission",
            vertical="fintech"
        )

        assert len(results) > 0

    def test_retrieve_with_context(self, rag_pipeline):
        """Test retrieval with formatted context"""
        rag_pipeline.index_text(
            text="RBI mandates that all payment aggregators maintain escrow accounts.",
            vertical="fintech",
            source="rbi_guidelines"
        )

        result = rag_pipeline.retrieve_with_context(
            query="escrow requirements",
            vertical="fintech"
        )

        assert result["found"]
        assert "escrow" in result["context"].lower()
        assert len(result["sources"]) > 0


class TestFintechRAG:
    """Test FinTech-specific RAG"""

    @pytest.fixture
    def fintech_rag(self):
        return FintechRAG()

    def test_retrieve_compliance(self, fintech_rag):
        """Test compliance document retrieval"""
        # Index compliance content
        fintech_rag.index_text(
            text="PCI-DSS requires that cardholder data be encrypted using AES-256.",
            vertical="fintech",
            source="pci_standard.md",
            metadata={"type": "compliance"}
        )

        results = fintech_rag.retrieve_compliance("encryption requirements")

        assert len(results) > 0

    def test_compliance_context(self, fintech_rag):
        """Test getting compliance context"""
        fintech_rag.index_text(
            text="Transaction monitoring is required for fraud detection per RBI guidelines.",
            vertical="fintech",
            source="rbi_fraud.md"
        )

        context = fintech_rag.get_compliance_context("fraud detection requirements")

        assert context["found"]
        assert "fraud" in context["context"].lower()
