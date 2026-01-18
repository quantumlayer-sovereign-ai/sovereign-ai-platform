"""
RAG Pipeline - Main orchestration for Retrieval Augmented Generation

Combines:
- Document loading and chunking
- Embedding generation
- Vector storage and retrieval
- Context augmentation for LLM
"""

from pathlib import Path
from typing import Any, ClassVar

import structlog

from .embeddings import EmbeddingModel
from .loader import Document, DocumentLoader
from .vectorstore import MultiVerticalStore

logger = structlog.get_logger()


class RAGPipeline:
    """
    Complete RAG pipeline for document retrieval and context augmentation

    Features:
    - Multi-vertical support (fintech, healthcare, etc.)
    - Configurable retrieval strategies
    - Context formatting for different LLMs
    - Source attribution for compliance
    """

    def __init__(
        self,
        persist_directory: str | None = None,
        embedding_model: str = "minilm",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chromadb_host: str | None = None,
        chromadb_port: int = 8000
    ):
        self.persist_directory = persist_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize components
        self.embedding_model = EmbeddingModel(model_name=embedding_model)
        self.multi_store = MultiVerticalStore(
            persist_directory=persist_directory,
            embedding_model=self.embedding_model,
            host=chromadb_host,
            port=chromadb_port
        )

        self.loaders: dict[str, DocumentLoader] = {}

    def get_loader(self, vertical: str) -> DocumentLoader:
        """Get or create loader for a vertical"""
        if vertical not in self.loaders:
            self.loaders[vertical] = DocumentLoader(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                vertical=vertical
            )
        return self.loaders[vertical]

    def index_directory(
        self,
        directory: Path,
        vertical: str,
        recursive: bool = True,
        extensions: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Index all documents from a directory

        Args:
            directory: Source directory
            vertical: Vertical name (fintech, healthcare, etc.)
            recursive: Search subdirectories
            extensions: File extensions to include

        Returns:
            Indexing statistics
        """
        directory = Path(directory)

        logger.info("indexing_directory",
                   directory=str(directory),
                   vertical=vertical)

        # Load and chunk documents
        loader = self.get_loader(vertical)
        chunks = loader.load_and_chunk(directory, recursive=recursive)

        if not chunks:
            logger.warning("no_documents_found", directory=str(directory))
            return {"documents": 0, "chunks": 0}

        # Add to vector store
        store = self.multi_store.get_store(vertical)
        added = store.add_chunks(chunks)

        stats = {
            "directory": str(directory),
            "vertical": vertical,
            "chunks_indexed": added,
            "store_stats": store.get_stats()
        }

        logger.info("indexing_complete", **stats)
        return stats

    def index_document(
        self,
        file_path: Path,
        vertical: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Index a single document

        Args:
            file_path: Path to document
            vertical: Vertical name
            metadata: Additional metadata

        Returns:
            Indexing statistics
        """
        file_path = Path(file_path)
        loader = self.get_loader(vertical)

        doc = loader.load_file(file_path)
        if not doc:
            return {"success": False, "error": "Failed to load document"}

        if metadata:
            doc.metadata.update(metadata)

        chunks = loader.chunk_document(doc)
        store = self.multi_store.get_store(vertical)
        added = store.add_chunks(chunks)

        return {
            "success": True,
            "file": str(file_path),
            "chunks_indexed": added
        }

    def index_text(
        self,
        text: str,
        vertical: str,
        source: str = "direct_input",
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Index raw text content

        Args:
            text: Text content to index
            vertical: Vertical name
            source: Source identifier
            metadata: Additional metadata

        Returns:
            Indexing statistics
        """
        doc = Document(
            content=text,
            metadata={
                "source": source,
                "vertical": vertical,
                "file_type": "text",
                **(metadata or {})
            }
        )

        loader = self.get_loader(vertical)
        chunks = loader.chunk_document(doc)
        store = self.multi_store.get_store(vertical)
        added = store.add_chunks(chunks)

        return {
            "success": True,
            "source": source,
            "chunks_indexed": added
        }

    def retrieve(
        self,
        query: str,
        vertical: str,
        n_results: int = 5,
        min_score: float = 0.0,
        file_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant documents for a query

        Args:
            query: Search query
            vertical: Vertical to search in
            n_results: Maximum number of results
            min_score: Minimum similarity score
            file_types: Filter by file types

        Returns:
            List of relevant documents with scores
        """
        store = self.multi_store.get_store(vertical)

        # Build filter
        where = None
        if file_types:
            where = {"file_type": {"$in": file_types}}

        results = store.search(
            query=query,
            n_results=n_results,
            where=where
        )

        # Filter by minimum score
        if min_score > 0:
            results = [r for r in results if r["score"] >= min_score]

        return results

    def retrieve_with_context(
        self,
        query: str,
        vertical: str,
        n_results: int = 5,
        context_template: str | None = None
    ) -> dict[str, Any]:
        """
        Retrieve and format context for LLM

        Args:
            query: User query
            vertical: Vertical to search
            n_results: Number of documents to retrieve
            context_template: Optional template for formatting

        Returns:
            Dict with formatted context and sources
        """
        results = self.retrieve(
            query=query,
            vertical=vertical,
            n_results=n_results
        )

        if not results:
            return {
                "context": "",
                "sources": [],
                "found": False
            }

        # Default context template
        if context_template is None:
            context_template = """Relevant information from knowledge base:

{documents}

Use this information to answer the following question. If the information doesn't contain the answer, say so."""

        # Format documents
        doc_texts = []
        sources = []

        for i, result in enumerate(results, 1):
            doc_texts.append(f"[{i}] {result['content']}")
            sources.append({
                "index": i,
                "source": result["metadata"].get("source", "unknown"),
                "score": result["score"],
                "file_type": result["metadata"].get("file_type", "unknown")
            })

        context = context_template.format(
            documents="\n\n".join(doc_texts)
        )

        return {
            "context": context,
            "sources": sources,
            "found": True,
            "num_results": len(results)
        }

    def augment_prompt(
        self,
        query: str,
        vertical: str,
        system_prompt: str,
        n_results: int = 5
    ) -> str:
        """
        Augment system prompt with retrieved context

        Args:
            query: User query
            vertical: Vertical to search
            system_prompt: Original system prompt
            n_results: Number of documents to retrieve

        Returns:
            Augmented system prompt
        """
        retrieval = self.retrieve_with_context(
            query=query,
            vertical=vertical,
            n_results=n_results
        )

        if not retrieval["found"]:
            return system_prompt

        augmented = f"""{system_prompt}

---
{retrieval["context"]}
---

Sources used:
{chr(10).join(f"- [{s['index']}] {s['source']} (relevance: {s['score']:.2f})" for s in retrieval["sources"])}
"""
        return augmented

    def get_stats(self, vertical: str | None = None) -> dict[str, Any]:
        """Get pipeline statistics"""
        if vertical:
            store = self.multi_store.get_store(vertical)
            return store.get_stats()
        return self.multi_store.get_all_stats()

    def clear_vertical(self, vertical: str):
        """Clear all data for a vertical"""
        store = self.multi_store.get_store(vertical)
        store.delete_collection()
        logger.info("vertical_cleared", vertical=vertical)


class FintechRAG(RAGPipeline):
    """
    FinTech-specific RAG pipeline

    Pre-configured with:
    - PCI-DSS knowledge
    - RBI/SEBI guidelines
    - Payment system patterns
    - Security best practices
    """

    FINTECH_SOURCES: ClassVar[dict[str, str]] = {
        "pci_dss": "PCI Data Security Standard",
        "rbi_guidelines": "RBI Payment Aggregator Guidelines",
        "sebi_regulations": "SEBI Regulations",
        "payment_patterns": "Payment System Design Patterns",
        "security_practices": "Financial Security Best Practices"
    }

    def __init__(self, persist_directory: str | None = None, **kwargs):
        super().__init__(
            persist_directory=persist_directory,
            **kwargs
        )
        self.vertical = "fintech"

    def index_compliance_docs(self, docs_directory: Path) -> dict[str, Any]:
        """Index compliance documentation"""
        return self.index_directory(
            directory=docs_directory,
            vertical=self.vertical,
            extensions=[".txt", ".md", ".pdf"]
        )

    def index_code_patterns(self, patterns_directory: Path) -> dict[str, Any]:
        """Index code patterns and examples"""
        return self.index_directory(
            directory=patterns_directory,
            vertical=self.vertical,
            extensions=[".py", ".java", ".go", ".ts"]
        )

    def retrieve_compliance(
        self,
        query: str,
        n_results: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieve compliance-related documents"""
        return self.retrieve(
            query=query,
            vertical=self.vertical,
            n_results=n_results,
            file_types=["text", "markdown", "pdf"]
        )

    def retrieve_code_examples(
        self,
        query: str,
        n_results: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieve code examples"""
        return self.retrieve(
            query=query,
            vertical=self.vertical,
            n_results=n_results,
            file_types=["python", "java", "go", "typescript"]
        )

    def get_compliance_context(self, query: str) -> dict[str, Any]:
        """Get compliance context for a query"""
        return self.retrieve_with_context(
            query=query,
            vertical=self.vertical,
            n_results=5,
            context_template="""Relevant compliance information and regulations:

{documents}

Apply these compliance requirements when providing your response. Cite the relevant sections."""
        )
