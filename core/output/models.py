"""
Project Output Data Models

Defines the data structures for project generation:
- CodeBlock: Extracted code with metadata
- ProjectFile: File within a project
- ProjectManifest: Complete project metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CodeBlock:
    """A block of code extracted from agent output"""
    content: str
    language: str
    agent: str
    suggested_filename: str

    def __post_init__(self):
        # Normalize language names
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "jsx": "javascript",
            "tsx": "typescript",
            "yml": "yaml",
            "sh": "bash",
            "shell": "bash",
        }
        self.language = lang_map.get(self.language.lower(), self.language.lower())


@dataclass
class ProjectFile:
    """A file within a generated project"""
    path: str           # e.g., "src/payment/processor.py"
    content: str
    language: str
    size: int = 0

    def __post_init__(self):
        self.size = len(self.content.encode('utf-8'))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "path": self.path,
            "content": self.content,
            "language": self.language,
            "size": self.size,
        }


@dataclass
class ProjectManifest:
    """Complete metadata for a generated project"""
    task_id: str
    task: str
    created_at: datetime
    files: list[ProjectFile]
    agents_used: list[str]
    total_files: int = 0
    total_size: int = 0

    def __post_init__(self):
        self.total_files = len(self.files)
        self.total_size = sum(f.size for f in self.files)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "task": self.task,
            "created_at": self.created_at.isoformat(),
            "files": [f.to_dict() for f in self.files],
            "agents_used": self.agents_used,
            "total_files": self.total_files,
            "total_size": self.total_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectManifest":
        """Create from dictionary"""
        files = [
            ProjectFile(
                path=f["path"],
                content=f.get("content", ""),
                language=f["language"],
            )
            for f in data.get("files", [])
        ]
        return cls(
            task_id=data["task_id"],
            task=data["task"],
            created_at=datetime.fromisoformat(data["created_at"]),
            files=files,
            agents_used=data.get("agents_used", []),
        )
