"""
Unit Tests for Vector Store

Tests:
- Store initialization
- Adding chunks
- Searching
- Filtering
- Persistence
"""

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import requires_chromadb


@requires_chromadb
class TestVectorStoreUnit:
    """Unit tests for VectorStore class"""

    @pytest.fixture
    def mock_chromadb_client(self):
        """Mock ChromaDB client"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.add = MagicMock()
        mock_collection.query = MagicMock(return_value={
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"source": "test.txt"}, {"source": "test2.txt"}]],
            "distances": [[0.1, 0.2]]
        })

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client.delete_collection = MagicMock()
        mock_client.list_collections.return_value = []

        return mock_client, mock_collection

    @pytest.fixture
    def mock_embedding_model(self):
        """Mock embedding model"""
        model = MagicMock()
        model.is_loaded = True
        model.embed.return_value = [[0.1] * 384, [0.2] * 384]
        model.embed_query.return_value = [0.1] * 384
        model.dimension = 384
        model.load = MagicMock()
        return model

    @pytest.mark.unit
    def test_initialization_defaults(self):
        """Test store initialization with defaults"""
        from core.rag.vectorstore import VectorStore
        store = VectorStore()

        assert store.collection_name == "default"
        assert store.persist_directory is None
        assert store.client is None

    @pytest.mark.unit
    def test_initialization_with_persist(self):
        """Test store initialization with persistence"""
        from core.rag.vectorstore import VectorStore
        store = VectorStore(
            collection_name="test_collection",
            persist_directory="/tmp/vectordb"
        )

        assert store.collection_name == "test_collection"
        assert store.persist_directory == "/tmp/vectordb"

    @pytest.mark.unit
    def test_initialization_with_remote(self):
        """Test store initialization with remote host"""
        from core.rag.vectorstore import VectorStore
        store = VectorStore(
            collection_name="test",
            host="localhost",
            port=8000
        )

        assert store.host == "localhost"
        assert store.port == 8000

    @pytest.mark.unit
    def test_connect_memory(self, mock_chromadb_client, mock_embedding_model):
        """Test in-memory connection"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )
                store.connect()

                assert store.is_connected
                mock_client.get_or_create_collection.assert_called()

    @pytest.mark.unit
    def test_connect_persistent(self, mock_chromadb_client, mock_embedding_model, tmp_path):
        """Test persistent connection"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.PersistentClient', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    persist_directory=str(tmp_path),
                    embedding_model=mock_embedding_model
                )
                store.connect()

                assert store.is_connected

    @pytest.mark.unit
    def test_add_chunks(self, mock_chromadb_client, mock_embedding_model):
        """Test adding chunks to store"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.loader import Chunk
                from core.rag.vectorstore import VectorStore

                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                chunks = [
                    Chunk(
                        chunk_id="0",
                        doc_id="doc1",
                        content="Test content 1",
                        metadata={"source": "test.txt"}
                    ),
                    Chunk(
                        chunk_id="1",
                        doc_id="doc1",
                        content="Test content 2",
                        metadata={"source": "test2.txt"}
                    )
                ]

                count = store.add_chunks(chunks)

                assert count == 2
                mock_collection.add.assert_called()

    @pytest.mark.unit
    def test_add_empty_chunks(self, mock_chromadb_client, mock_embedding_model):
        """Test adding empty chunk list"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                count = store.add_chunks([])

                assert count == 0

    @pytest.mark.unit
    def test_search_basic(self, mock_chromadb_client, mock_embedding_model):
        """Test basic search"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                results = store.search("test query", n_results=2)

                assert len(results) == 2
                mock_embedding_model.embed_query.assert_called_with("test query")
                mock_collection.query.assert_called()

    @pytest.mark.unit
    def test_search_with_filter(self, mock_chromadb_client, mock_embedding_model):
        """Test search with metadata filter"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                results = store.search(
                    "test query",
                    n_results=5,
                    where={"vertical": "fintech"}
                )

                call_args = mock_collection.query.call_args
                assert call_args.kwargs.get("where") == {"vertical": "fintech"}

    @pytest.mark.unit
    def test_search_result_format(self, mock_chromadb_client, mock_embedding_model):
        """Test search result format"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                results = store.search("test query")

                for result in results:
                    assert "content" in result
                    assert "metadata" in result
                    assert "score" in result
                    assert "distance" in result

    @pytest.mark.unit
    def test_get_stats(self, mock_chromadb_client, mock_embedding_model):
        """Test getting store statistics"""
        mock_client, mock_collection = mock_chromadb_client
        mock_collection.count.return_value = 100

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                stats = store.get_stats()

                assert stats["count"] == 100
                assert stats["collection"] == "test"

    @pytest.mark.unit
    def test_delete_collection(self, mock_chromadb_client, mock_embedding_model):
        """Test deleting collection"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                store.delete_collection()

                mock_client.delete_collection.assert_called_with("test")

    @pytest.mark.unit
    def test_search_by_vertical(self, mock_chromadb_client, mock_embedding_model):
        """Test search by vertical"""
        mock_client, mock_collection = mock_chromadb_client

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.vectorstore import VectorStore
                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                store.search_by_vertical("test query", "fintech")

                call_args = mock_collection.query.call_args
                assert call_args.kwargs.get("where") == {"vertical": "fintech"}

    @pytest.mark.unit
    def test_batch_add_large(self, mock_chromadb_client, mock_embedding_model):
        """Test batched adding for large chunk sets"""
        mock_client, mock_collection = mock_chromadb_client

        def mock_embed(texts, **kwargs):
            return [[0.1] * 384 for _ in texts]

        mock_embedding_model.embed.side_effect = mock_embed

        with patch('chromadb.Client', return_value=mock_client):
            with patch('chromadb.config.Settings'):
                from core.rag.loader import Chunk
                from core.rag.vectorstore import VectorStore

                store = VectorStore(
                    collection_name="test",
                    embedding_model=mock_embedding_model
                )

                # Create 250 chunks
                chunks = [
                    Chunk(
                        chunk_id=str(i),
                        doc_id="doc1",
                        content=f"Content {i}",
                        metadata={"source": "test.txt"}
                    )
                    for i in range(250)
                ]

                count = store.add_chunks(chunks, batch_size=100)

                assert count == 250
                # Should have called add multiple times due to batching
                assert mock_collection.add.call_count >= 2
