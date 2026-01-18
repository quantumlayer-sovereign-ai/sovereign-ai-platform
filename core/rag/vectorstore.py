"""
Vector Store - ChromaDB integration for document retrieval

Supports:
- Persistent and in-memory storage
- Collection management per vertical
- Metadata filtering
- Similarity search with scores
"""

from typing import Any

import structlog

from .embeddings import EmbeddingModel
from .loader import Chunk

logger = structlog.get_logger()


class VectorStore:
    """
    ChromaDB vector store wrapper

    Features:
    - Collection per vertical (fintech, healthcare, etc.)
    - Persistent storage for production
    - Metadata filtering for precise retrieval
    - Batch operations for efficient indexing
    """

    def __init__(
        self,
        collection_name: str = "default",
        persist_directory: str | None = None,
        embedding_model: EmbeddingModel | None = None,
        host: str | None = None,
        port: int = 8000
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model or EmbeddingModel()
        self.host = host
        self.port = port

        self.client = None
        self.collection = None

    def connect(self):
        """Connect to ChromaDB"""
        import chromadb
        from chromadb.config import Settings

        if self.host:
            # Connect to remote ChromaDB server
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port
            )
            logger.info("chromadb_connected_remote",
                       host=self.host,
                       port=self.port)
        elif self.persist_directory:
            # Use persistent storage
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("chromadb_connected_persistent",
                       path=self.persist_directory)
        else:
            # In-memory for testing
            self.client = chromadb.Client(
                Settings(anonymized_telemetry=False)
            )
            logger.info("chromadb_connected_memory")

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info("collection_ready",
                   name=self.collection_name,
                   count=self.collection.count())

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.collection is not None

    def add_chunks(
        self,
        chunks: list[Chunk],
        batch_size: int = 100
    ) -> int:
        """
        Add chunks to the vector store

        Args:
            chunks: List of document chunks
            batch_size: Batch size for processing

        Returns:
            Number of chunks added
        """
        if not self.is_connected:
            self.connect()

        if not self.embedding_model.is_loaded:
            self.embedding_model.load()

        total_added = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            ids = [chunk.id for chunk in batch]
            documents = [chunk.content for chunk in batch]
            metadatas = [chunk.metadata for chunk in batch]

            # Generate embeddings
            embeddings = self.embedding_model.embed(documents)

            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            total_added += len(batch)
            logger.debug("chunks_added",
                        batch=i // batch_size + 1,
                        count=len(batch))

        logger.info("chunks_indexed",
                   total=total_added,
                   collection=self.collection_name)

        return total_added

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for relevant documents

        Args:
            query: Search query
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter

        Returns:
            List of results with content, metadata, and scores
        """
        if not self.is_connected:
            self.connect()

        # Generate query embedding
        query_embedding = self.embedding_model.embed_query(query)

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        formatted = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "score": 1 - results["distances"][0][i] if results["distances"] else 1,
                    "id": results["ids"][0][i] if results["ids"] else None
                })

        return formatted

    def search_by_vertical(
        self,
        query: str,
        vertical: str,
        n_results: int = 5
    ) -> list[dict[str, Any]]:
        """Search within a specific vertical"""
        return self.search(
            query=query,
            n_results=n_results,
            where={"vertical": vertical}
        )

    def search_by_file_type(
        self,
        query: str,
        file_type: str,
        n_results: int = 5
    ) -> list[dict[str, Any]]:
        """Search within specific file types"""
        return self.search(
            query=query,
            n_results=n_results,
            where={"file_type": file_type}
        )

    def delete_by_source(self, source: str):
        """Delete all chunks from a specific source"""
        if not self.is_connected:
            self.connect()

        self.collection.delete(
            where={"source": source}
        )
        logger.info("chunks_deleted", source=source)

    def delete_collection(self):
        """Delete the entire collection"""
        if not self.is_connected:
            self.connect()

        self.client.delete_collection(self.collection_name)
        self.collection = None
        logger.info("collection_deleted", name=self.collection_name)

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics"""
        if not self.is_connected:
            self.connect()

        return {
            "collection": self.collection_name,
            "count": self.collection.count(),
            "persist_directory": self.persist_directory,
            "remote": self.host is not None
        }

    def list_collections(self) -> list[str]:
        """List all collections"""
        if not self.is_connected:
            self.connect()

        collections = self.client.list_collections()
        return [c.name for c in collections]


class MultiVerticalStore:
    """
    Manages multiple vector stores for different verticals

    Each vertical gets its own collection for isolation
    """

    def __init__(
        self,
        persist_directory: str | None = None,
        embedding_model: EmbeddingModel | None = None,
        host: str | None = None,
        port: int = 8000
    ):
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model or EmbeddingModel()
        self.host = host
        self.port = port
        self.stores: dict[str, VectorStore] = {}

    def get_store(self, vertical: str) -> VectorStore:
        """Get or create store for a vertical"""
        if vertical not in self.stores:
            self.stores[vertical] = VectorStore(
                collection_name=f"sovereign_{vertical}",
                persist_directory=self.persist_directory,
                embedding_model=self.embedding_model,
                host=self.host,
                port=self.port
            )
            self.stores[vertical].connect()

        return self.stores[vertical]

    def search_across_verticals(
        self,
        query: str,
        verticals: list[str],
        n_results_per_vertical: int = 3
    ) -> dict[str, list[dict[str, Any]]]:
        """Search across multiple verticals"""
        results = {}

        for vertical in verticals:
            store = self.get_store(vertical)
            results[vertical] = store.search(
                query=query,
                n_results=n_results_per_vertical
            )

        return results

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get stats for all verticals"""
        return {
            vertical: store.get_stats()
            for vertical, store in self.stores.items()
        }
