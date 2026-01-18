"""
Embedding Model - Sentence Transformers integration

Uses local embedding models for air-gapped deployment
"""

from typing import ClassVar

import structlog

logger = structlog.get_logger()


class EmbeddingModel:
    """
    Embedding model wrapper using Sentence Transformers

    Supports multiple embedding models optimized for different use cases:
    - all-MiniLM-L6-v2: Fast, good for general use (384 dim)
    - all-mpnet-base-v2: Better quality (768 dim)
    - BAAI/bge-large-en-v1.5: Best quality for retrieval (1024 dim)
    """

    MODELS: ClassVar[dict[str, str]] = {
        "minilm": "sentence-transformers/all-MiniLM-L6-v2",
        "mpnet": "sentence-transformers/all-mpnet-base-v2",
        "bge-large": "BAAI/bge-large-en-v1.5",
        "bge-small": "BAAI/bge-small-en-v1.5",
    }

    def __init__(
        self,
        model_name: str = "minilm",
        device: str | None = None,
        cache_dir: str | None = None
    ):
        self.model_name = self.MODELS.get(model_name, model_name)
        self.device = device
        self.cache_dir = cache_dir
        self.model = None
        self._dimension = None

    def load(self):
        """Load the embedding model"""
        from sentence_transformers import SentenceTransformer

        logger.info("loading_embedding_model", model=self.model_name)

        self.model = SentenceTransformer(
            self.model_name,
            device=self.device,
            cache_folder=self.cache_dir
        )
        self._dimension = self.model.get_sentence_embedding_dimension()

        logger.info("embedding_model_loaded",
                   model=self.model_name,
                   dimension=self._dimension)

    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        if self._dimension is None:
            self.load()
        return self._dimension

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def embed(self, texts: list[str], show_progress: bool = False) -> list[list[float]]:
        """
        Generate embeddings for texts

        Args:
            texts: List of text strings to embed
            show_progress: Show progress bar for large batches

        Returns:
            List of embedding vectors
        """
        if not self.is_loaded:
            self.load()

        embeddings = self.model.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string"""
        return self.embed([query])[0]

    def embed_documents(self, documents: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Embed documents in batches

        Args:
            documents: List of document texts
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        if not self.is_loaded:
            self.load()

        all_embeddings = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            embeddings = self.embed(batch)
            all_embeddings.extend(embeddings)

            if i > 0 and i % (batch_size * 10) == 0:
                logger.info("embedding_progress",
                           processed=i,
                           total=len(documents))

        return all_embeddings

    def similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        import numpy as np

        e1 = np.array(embedding1)
        e2 = np.array(embedding2)

        return float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2)))
