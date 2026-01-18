"""
Unit Tests for Document Loader

Tests:
- File loading
- Document chunking
- Metadata extraction
- Supported file types
- Error handling
"""

from pathlib import Path

import pytest


class TestDocumentLoaderUnit:
    """Unit tests for DocumentLoader class"""

    @pytest.fixture
    def loader(self):
        """Create document loader instance"""
        from core.rag.loader import DocumentLoader
        return DocumentLoader(chunk_size=500, chunk_overlap=50)

    @pytest.mark.unit
    def test_initialization_defaults(self):
        """Test loader initialization with defaults"""
        from core.rag.loader import DocumentLoader
        loader = DocumentLoader()

        assert loader.chunk_size == 1000
        assert loader.chunk_overlap == 200

    @pytest.mark.unit
    def test_initialization_custom(self):
        """Test loader initialization with custom values"""
        from core.rag.loader import DocumentLoader
        loader = DocumentLoader(chunk_size=500, chunk_overlap=100)

        assert loader.chunk_size == 500
        assert loader.chunk_overlap == 100

    @pytest.mark.unit
    def test_initialization_with_vertical(self):
        """Test loader initialization with vertical"""
        from core.rag.loader import DocumentLoader
        loader = DocumentLoader(vertical="fintech")

        assert loader.vertical == "fintech"

    @pytest.mark.unit
    def test_supported_extensions(self):
        """Test supported file extensions"""
        from core.rag.loader import DocumentLoader

        assert ".txt" in DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".md" in DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".py" in DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".json" in DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".pdf" in DocumentLoader.SUPPORTED_EXTENSIONS

    @pytest.mark.unit
    def test_load_text_file(self, loader, tmp_path):
        """Test loading a text file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is test content for the document loader.")

        doc = loader.load_file(test_file)

        assert doc is not None
        assert doc.content == "This is test content for the document loader."
        assert doc.metadata["source"] == str(test_file)
        assert doc.metadata["file_type"] == "text"

    @pytest.mark.unit
    def test_load_markdown_file(self, loader, tmp_path):
        """Test loading a markdown file"""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Header\n\nThis is **markdown** content.")

        doc = loader.load_file(test_file)

        assert doc is not None
        assert "# Header" in doc.content
        assert doc.metadata["file_type"] == "markdown"

    @pytest.mark.unit
    def test_load_python_file(self, loader, tmp_path):
        """Test loading a Python file"""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('Hello, World!')")

        doc = loader.load_file(test_file)

        assert doc is not None
        assert "def hello()" in doc.content
        assert doc.metadata["file_type"] == "python"

    @pytest.mark.unit
    def test_load_json_file(self, loader, tmp_path):
        """Test loading a JSON file"""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value", "number": 42}')

        doc = loader.load_file(test_file)

        assert doc is not None
        assert doc.metadata["file_type"] == "json"

    @pytest.mark.unit
    def test_load_nonexistent_file(self, loader):
        """Test loading non-existent file"""
        result = loader.load_file(Path("/nonexistent/file.txt"))

        assert result is None

    @pytest.mark.unit
    def test_load_unsupported_extension(self, loader, tmp_path):
        """Test loading unsupported file type"""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("Some content")

        result = loader.load_file(test_file)

        assert result is None

    @pytest.mark.unit
    def test_chunk_document_small(self, loader):
        """Test chunking small document (no split needed)"""
        from core.rag.loader import Document

        doc = Document(
            content="Small content",
            metadata={"source": "test.txt"}
        )

        chunks = loader.chunk_document(doc)

        assert len(chunks) == 1
        assert chunks[0].content == "Small content"

    @pytest.mark.unit
    def test_chunk_document_large(self):
        """Test chunking large document"""
        from core.rag.loader import Document, DocumentLoader

        loader = DocumentLoader(chunk_size=100, chunk_overlap=20)

        # Create content larger than chunk_size
        large_content = "This is a sentence. " * 50  # ~1000 chars

        doc = Document(
            content=large_content,
            metadata={"source": "test.txt"}
        )

        chunks = loader.chunk_document(doc)

        assert len(chunks) > 1

    @pytest.mark.unit
    def test_chunk_preserves_metadata(self, loader):
        """Test that chunking preserves document metadata"""
        from core.rag.loader import Document

        doc = Document(
            content="This is content. " * 100,  # Make it large enough to chunk
            metadata={"source": "test.txt", "vertical": "fintech"}
        )

        chunks = loader.chunk_document(doc)

        for chunk in chunks:
            assert chunk.metadata["source"] == "test.txt"
            assert chunk.metadata["vertical"] == "fintech"

    @pytest.mark.unit
    def test_load_directory(self, loader, tmp_path):
        """Test loading entire directory"""
        # Create test files
        (tmp_path / "file1.txt").write_text("Content 1")
        (tmp_path / "file2.md").write_text("# Content 2")
        (tmp_path / "file3.py").write_text("print('hello')")

        docs = loader.load_directory(tmp_path)

        assert len(docs) == 3

    @pytest.mark.unit
    def test_load_directory_recursive(self, loader, tmp_path):
        """Test recursive directory loading"""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.txt").write_text("Root content")
        (subdir / "file2.txt").write_text("Nested content")

        docs = loader.load_directory(tmp_path, recursive=True)

        assert len(docs) == 2

    @pytest.mark.unit
    def test_load_directory_non_recursive(self, loader, tmp_path):
        """Test non-recursive directory loading"""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.txt").write_text("Root content")
        (subdir / "file2.txt").write_text("Nested content")

        docs = loader.load_directory(tmp_path, recursive=False)

        assert len(docs) == 1

    @pytest.mark.unit
    def test_load_directory_with_extension_filter(self, loader, tmp_path):
        """Test directory loading with extension filter"""
        (tmp_path / "file1.txt").write_text("Text content")
        (tmp_path / "file2.py").write_text("Python content")
        (tmp_path / "file3.md").write_text("Markdown content")

        docs = loader.load_directory(tmp_path, extensions=[".txt"])

        assert len(docs) == 1
        assert docs[0].metadata["file_type"] == "text"

    @pytest.mark.unit
    def test_load_directory_nonexistent(self, loader):
        """Test loading non-existent directory"""
        docs = loader.load_directory(Path("/nonexistent/directory"))

        assert len(docs) == 0

    @pytest.mark.unit
    def test_chunk_ids_unique(self, loader):
        """Test that chunk IDs are unique"""
        from core.rag.loader import Document

        doc = Document(
            content="Sentence one. " * 50 + "\n\n" + "Sentence two. " * 50,
            metadata={"source": "test.txt"}
        )

        chunks = loader.chunk_document(doc)
        chunk_ids = [c.id for c in chunks]

        assert len(chunk_ids) == len(set(chunk_ids))  # All unique

    @pytest.mark.unit
    def test_load_and_chunk(self, loader, tmp_path):
        """Test combined load and chunk operation"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content for testing. " * 100)

        chunks = loader.load_and_chunk(test_file)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.content
            assert chunk.metadata["source"] == str(test_file)

    @pytest.mark.unit
    def test_load_and_chunk_directory(self, loader, tmp_path):
        """Test load and chunk on directory"""
        (tmp_path / "file1.txt").write_text("Content 1. " * 50)
        (tmp_path / "file2.txt").write_text("Content 2. " * 50)

        chunks = loader.load_and_chunk(tmp_path)

        assert len(chunks) >= 2


class TestDocumentUnit:
    """Unit tests for Document dataclass"""

    @pytest.mark.unit
    def test_document_creation(self):
        """Test Document creation"""
        from core.rag.loader import Document

        doc = Document(
            content="Test content",
            metadata={"source": "test.txt"}
        )

        assert doc.content == "Test content"
        assert doc.metadata["source"] == "test.txt"
        assert doc.doc_id is not None

    @pytest.mark.unit
    def test_document_auto_id(self):
        """Test Document auto-generates ID"""
        from core.rag.loader import Document

        doc = Document(content="Test content")

        assert doc.doc_id is not None
        assert len(doc.doc_id) == 12  # MD5 hash truncated

    @pytest.mark.unit
    def test_document_custom_id(self):
        """Test Document with custom ID"""
        from core.rag.loader import Document

        doc = Document(content="Test", doc_id="custom123")

        assert doc.doc_id == "custom123"


class TestChunkUnit:
    """Unit tests for Chunk dataclass"""

    @pytest.mark.unit
    def test_chunk_creation(self):
        """Test Chunk creation"""
        from core.rag.loader import Chunk

        chunk = Chunk(
            content="Chunk content",
            doc_id="doc123",
            chunk_id="0",
            metadata={"source": "test.txt"}
        )

        assert chunk.content == "Chunk content"
        assert chunk.doc_id == "doc123"
        assert chunk.chunk_id == "0"

    @pytest.mark.unit
    def test_chunk_id_property(self):
        """Test Chunk id property"""
        from core.rag.loader import Chunk

        chunk = Chunk(
            content="Test",
            doc_id="doc123",
            chunk_id="5"
        )

        assert chunk.id == "doc123_5"
