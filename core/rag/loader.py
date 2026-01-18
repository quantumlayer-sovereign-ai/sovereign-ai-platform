"""
Document Loader - Load and chunk documents for RAG

Supports:
- Text files (.txt, .md)
- PDF files
- Code files (.py, .js, .java, etc.)
- JSON/YAML configuration files
"""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import structlog
import yaml

logger = structlog.get_logger()


@dataclass
class Document:
    """Document with content and metadata"""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    doc_id: str | None = None

    def __post_init__(self):
        if self.doc_id is None:
            # Generate ID from content hash (not used for security)
            self.doc_id = hashlib.md5(self.content.encode(), usedforsecurity=False).hexdigest()[:12]


@dataclass
class Chunk:
    """Document chunk for embedding"""
    content: str
    doc_id: str
    chunk_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"{self.doc_id}_{self.chunk_id}"


class DocumentLoader:
    """
    Load documents from various sources

    Supports recursive directory loading with file type filtering
    """

    SUPPORTED_EXTENSIONS: ClassVar[dict[str, str]] = {
        # Text files
        ".txt": "text",
        ".md": "markdown",
        ".rst": "text",

        # Code files
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "header",
        ".sql": "sql",
        ".sh": "shell",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".toml": "toml",

        # Documents
        ".pdf": "pdf",
    }

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        vertical: str | None = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vertical = vertical

    def load_file(self, file_path: Path) -> Document | None:
        """Load a single file"""
        file_path = Path(file_path)

        if not file_path.exists():
            logger.warning("file_not_found", path=str(file_path))
            return None

        ext = file_path.suffix.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            logger.debug("unsupported_extension", path=str(file_path), ext=ext)
            return None

        file_type = self.SUPPORTED_EXTENSIONS[ext]

        try:
            if file_type == "pdf":
                content = self._load_pdf(file_path)
            elif file_type in ("yaml", "json"):
                content = self._load_structured(file_path, file_type)
            else:
                content = self._load_text(file_path)

            metadata = {
                "source": str(file_path),
                "filename": file_path.name,
                "file_type": file_type,
                "extension": ext,
                "vertical": self.vertical,
            }

            return Document(content=content, metadata=metadata)

        except Exception as e:
            logger.error("file_load_failed", path=str(file_path), error=str(e))
            return None

    def _load_text(self, file_path: Path) -> str:
        """Load text file"""
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _load_pdf(self, file_path: Path) -> str:
        """Load PDF file"""
        try:
            import pypdf

            reader = pypdf.PdfReader(file_path)
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)

        except ImportError:
            logger.warning("pypdf_not_installed",
                          message="Install pypdf to load PDF files")
            return ""

    def _load_structured(self, file_path: Path, file_type: str) -> str:
        """Load structured file (JSON/YAML) as formatted text"""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f) if file_type == "json" else yaml.safe_load(f)

        # Convert to readable text format
        return self._structured_to_text(data)

    def _structured_to_text(self, data: Any, indent: int = 0) -> str:
        """Convert structured data to readable text"""
        lines = []
        prefix = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._structured_to_text(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}-")
                    lines.append(self._structured_to_text(item, indent + 1))
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}{data}")

        return "\n".join(lines)

    def load_directory(
        self,
        directory: Path,
        recursive: bool = True,
        extensions: list[str] | None = None
    ) -> list[Document]:
        """
        Load all documents from a directory

        Args:
            directory: Directory path
            recursive: Whether to search recursively
            extensions: Optional list of extensions to filter

        Returns:
            List of loaded documents
        """
        directory = Path(directory)
        documents = []

        if not directory.exists():
            logger.warning("directory_not_found", path=str(directory))
            return documents

        pattern = "**/*" if recursive else "*"

        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()

            if extensions and ext not in extensions:
                continue

            doc = self.load_file(file_path)
            if doc:
                documents.append(doc)

        logger.info("directory_loaded",
                   path=str(directory),
                   document_count=len(documents))

        return documents

    def chunk_document(self, document: Document) -> list[Chunk]:
        """
        Split document into chunks for embedding

        Uses sliding window with overlap for better context preservation
        """
        content = document.content
        chunks = []

        # Split by paragraphs first
        paragraphs = content.split("\n\n")

        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) + 2 > self.chunk_size:
                if current_chunk:
                    chunks.append(Chunk(
                        content=current_chunk.strip(),
                        doc_id=document.doc_id,
                        chunk_id=str(chunk_index),
                        metadata={**document.metadata}
                    ))
                    chunk_index += 1

                    # Keep overlap
                    words = current_chunk.split()
                    overlap_words = words[-self.chunk_overlap // 5:] if len(words) > self.chunk_overlap // 5 else []
                    current_chunk = " ".join(overlap_words) + "\n\n" if overlap_words else ""

                # If single paragraph is too long, split by sentences
                if len(para) > self.chunk_size:
                    sentences = para.replace(". ", ".|").replace("! ", "!|").replace("? ", "?|").split("|")
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 > self.chunk_size and current_chunk:
                            chunks.append(Chunk(
                                content=current_chunk.strip(),
                                doc_id=document.doc_id,
                                chunk_id=str(chunk_index),
                                metadata={**document.metadata}
                            ))
                            chunk_index += 1
                            current_chunk = ""
                        current_chunk += sentence + " "
                else:
                    current_chunk += para + "\n\n"
            else:
                current_chunk += para + "\n\n"

        # Add final chunk
        if current_chunk.strip():
            chunks.append(Chunk(
                content=current_chunk.strip(),
                doc_id=document.doc_id,
                chunk_id=str(chunk_index),
                metadata={**document.metadata}
            ))

        return chunks

    def load_and_chunk(
        self,
        source: Path,
        recursive: bool = True
    ) -> list[Chunk]:
        """
        Load and chunk documents from a source

        Args:
            source: File or directory path
            recursive: Whether to search directories recursively

        Returns:
            List of chunks ready for embedding
        """
        source = Path(source)
        all_chunks = []

        if source.is_file():
            doc = self.load_file(source)
            if doc:
                all_chunks.extend(self.chunk_document(doc))
        else:
            docs = self.load_directory(source, recursive=recursive)
            for doc in docs:
                all_chunks.extend(self.chunk_document(doc))

        logger.info("documents_chunked",
                   source=str(source),
                   chunk_count=len(all_chunks))

        return all_chunks
