#!/usr/bin/env python3
"""
Index Code Templates into RAG System
====================================
This script indexes high-quality code templates into the RAG vector store
for retrieval during code generation.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rag.pipeline import RAGPipeline
import structlog

logger = structlog.get_logger()


TEMPLATE_COLLECTIONS = {
    "fastapi_templates": "data/code_templates/fastapi",
    "fintech_templates": "data/code_templates/fintech",
    "common_templates": "data/code_templates/common",
}


def index_templates():
    """Index all code templates into RAG collections."""

    rag = RAGPipeline(persist_directory="./data/vectordb")

    for collection_name, template_dir in TEMPLATE_COLLECTIONS.items():
        template_path = Path(template_dir)

        if not template_path.exists():
            logger.warning(f"Template directory not found: {template_path}")
            continue

        documents = []
        metadatas = []

        for file_path in template_path.glob("*.py"):
            content = file_path.read_text(encoding="utf-8")

            # Split into sections based on FILE: comments
            sections = content.split("# FILE:")

            for i, section in enumerate(sections):
                if not section.strip():
                    continue

                # Extract filename from section if present
                lines = section.strip().split("\n")
                if lines and "===" in (lines[1] if len(lines) > 1 else ""):
                    filename = lines[0].strip()
                    code = "\n".join(lines[2:])
                else:
                    filename = f"{file_path.stem}_section_{i}"
                    code = section

                if len(code.strip()) > 50:  # Only index meaningful code
                    documents.append(code.strip())
                    metadatas.append({
                        "source_file": str(file_path),
                        "template_name": file_path.stem,
                        "section": filename,
                        "collection": collection_name,
                        "type": "code_template",
                    })

        if documents:
            # Index each document into RAG
            for doc, meta in zip(documents, metadatas):
                rag.index_text(
                    text=doc,
                    vertical=collection_name,
                    source=meta.get("section", "unknown"),
                    metadata=meta,
                )
            logger.info(
                f"Indexed {len(documents)} sections from {collection_name}",
                collection=collection_name,
                count=len(documents),
            )

    logger.info("Template indexing complete")


def search_templates(query: str, collection: str = "fastapi_templates"):
    """Test search on indexed templates."""
    rag = RAGPipeline(persist_directory="./data/vectordb")

    results = rag.retrieve(
        query=query,
        vertical=collection,
        n_results=3,
    )

    print(f"\nSearch results for: {query}")
    print("=" * 50)
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Source: {result.get('metadata', {}).get('section', 'unknown')}")
        print(f"Score: {result.get('score', 'N/A')}")
        print(result.get('content', '')[:500] + "...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Index code templates for RAG")
    parser.add_argument("--search", type=str, help="Test search query")
    parser.add_argument("--collection", type=str, default="fastapi_templates")
    args = parser.parse_args()

    if args.search:
        search_templates(args.search, args.collection)
    else:
        index_templates()
