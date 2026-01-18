"""
Unit Tests for Embedding Model

Tests:
- Model initialization
- Single text embedding
- Batch embedding
- Query embedding
- Dimension validation
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


class TestEmbeddingModelUnit:
    """Unit tests for EmbeddingModel class"""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer"""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(5, 384).astype(np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 384
        return mock_model

    @pytest.mark.unit
    def test_model_initialization_default(self):
        """Test default model initialization"""
        from core.rag.embeddings import EmbeddingModel
        model = EmbeddingModel()

        assert model.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert model.model is None  # Not loaded yet

    @pytest.mark.unit
    def test_model_initialization_mpnet(self):
        """Test MPNet model initialization"""
        from core.rag.embeddings import EmbeddingModel
        model = EmbeddingModel(model_name="mpnet")

        assert "mpnet" in model.model_name

    @pytest.mark.unit
    def test_model_initialization_custom(self):
        """Test custom model name"""
        from core.rag.embeddings import EmbeddingModel
        model = EmbeddingModel(model_name="custom/model")

        assert model.model_name == "custom/model"

    @pytest.mark.unit
    def test_embed_single_text(self, mock_sentence_transformer):
        """Test embedding a single text"""
        mock_sentence_transformer.encode.return_value = np.random.rand(1, 384).astype(np.float32)

        with patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer):
            from core.rag.embeddings import EmbeddingModel
            model = EmbeddingModel()
            model.load()

            result = model.embed(["Test text"])

            assert len(result) == 1
            assert len(result[0]) == 384
            mock_sentence_transformer.encode.assert_called_once()

    @pytest.mark.unit
    def test_embed_batch(self, mock_sentence_transformer):
        """Test embedding multiple texts"""
        mock_sentence_transformer.encode.return_value = np.random.rand(3, 384).astype(np.float32)

        with patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer):
            from core.rag.embeddings import EmbeddingModel
            model = EmbeddingModel()
            model.load()

            texts = ["Text 1", "Text 2", "Text 3"]
            result = model.embed(texts)

            assert len(result) == 3
            for emb in result:
                assert len(emb) == 384

    @pytest.mark.unit
    def test_embed_query(self, mock_sentence_transformer):
        """Test embedding a query string"""
        mock_sentence_transformer.encode.return_value = np.random.rand(1, 384).astype(np.float32)

        with patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer):
            from core.rag.embeddings import EmbeddingModel
            model = EmbeddingModel()
            model.load()

            result = model.embed_query("What is PCI-DSS?")

            assert len(result) == 384

    @pytest.mark.unit
    def test_dimension_property(self, mock_sentence_transformer):
        """Test dimension property triggers load"""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer):
            from core.rag.embeddings import EmbeddingModel
            model = EmbeddingModel()

            dim = model.dimension

            assert dim == 384
            assert model.is_loaded

    @pytest.mark.unit
    def test_is_loaded_property(self):
        """Test is_loaded property"""
        from core.rag.embeddings import EmbeddingModel
        model = EmbeddingModel()

        assert model.is_loaded is False

    @pytest.mark.unit
    def test_available_models(self):
        """Test available models constant"""
        from core.rag.embeddings import EmbeddingModel

        assert "minilm" in EmbeddingModel.MODELS
        assert "mpnet" in EmbeddingModel.MODELS
        assert "bge-large" in EmbeddingModel.MODELS
        assert "bge-small" in EmbeddingModel.MODELS

    @pytest.mark.unit
    def test_similarity_calculation(self, mock_sentence_transformer):
        """Test similarity calculation between embeddings"""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer):
            from core.rag.embeddings import EmbeddingModel
            model = EmbeddingModel()

            # Create two similar embeddings
            emb1 = [1.0, 0.0, 0.0]
            emb2 = [1.0, 0.0, 0.0]

            similarity = model.similarity(emb1, emb2)

            assert similarity == pytest.approx(1.0, rel=0.01)

    @pytest.mark.unit
    def test_similarity_orthogonal(self, mock_sentence_transformer):
        """Test similarity of orthogonal vectors"""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer):
            from core.rag.embeddings import EmbeddingModel
            model = EmbeddingModel()

            emb1 = [1.0, 0.0, 0.0]
            emb2 = [0.0, 1.0, 0.0]

            similarity = model.similarity(emb1, emb2)

            assert similarity == pytest.approx(0.0, abs=0.01)

    @pytest.mark.unit
    def test_embed_documents_batched(self, mock_sentence_transformer):
        """Test batch document embedding"""
        def mock_encode(texts, **kwargs):
            return np.random.rand(len(texts), 384).astype(np.float32)

        mock_sentence_transformer.encode.side_effect = mock_encode

        with patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer):
            from core.rag.embeddings import EmbeddingModel
            model = EmbeddingModel()
            model.load()

            docs = [f"Document {i}" for i in range(100)]
            result = model.embed_documents(docs, batch_size=32)

            assert len(result) == 100
