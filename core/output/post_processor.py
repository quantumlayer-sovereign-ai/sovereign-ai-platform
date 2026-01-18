"""
Code Post-Processor
==================
Auto-fixes common issues in generated Python code:
- Missing imports
- Pydantic v1 → v2 migration
- Syntax validation
- Code formatting
"""

import ast
import re
import subprocess
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


# Common import mappings
IMPORT_MAPPINGS = {
    # Type hints
    "Optional": "from typing import Optional",
    "List": "from typing import List",
    "Dict": "from typing import Dict",
    "Any": "from typing import Any",
    "Union": "from typing import Union",
    "Callable": "from typing import Callable",
    "TypeVar": "from typing import TypeVar",
    "Generic": "from typing import Generic",
    "Sequence": "from collections.abc import Sequence",
    "AsyncGenerator": "from collections.abc import AsyncGenerator",

    # Data types
    "Decimal": "from decimal import Decimal",
    "datetime": "from datetime import datetime",
    "date": "from datetime import date",
    "timedelta": "from datetime import timedelta",
    "UUID": "from uuid import UUID",
    "uuid4": "from uuid import uuid4",
    "Enum": "from enum import Enum",

    # Pydantic v2
    "BaseModel": "from pydantic import BaseModel",
    "Field": "from pydantic import Field",
    "ConfigDict": "from pydantic import ConfigDict",
    "field_validator": "from pydantic import field_validator",
    "model_validator": "from pydantic import model_validator",
    "BaseSettings": "from pydantic_settings import BaseSettings",

    # FastAPI
    "FastAPI": "from fastapi import FastAPI",
    "APIRouter": "from fastapi import APIRouter",
    "Depends": "from fastapi import Depends",
    "HTTPException": "from fastapi import HTTPException",
    "status": "from fastapi import status",
    "Query": "from fastapi import Query",
    "Header": "from fastapi import Header",
    "Request": "from fastapi import Request",

    # SQLAlchemy
    "AsyncSession": "from sqlalchemy.ext.asyncio import AsyncSession",
    "create_async_engine": "from sqlalchemy.ext.asyncio import create_async_engine",
    "async_sessionmaker": "from sqlalchemy.ext.asyncio import async_sessionmaker",
    "DeclarativeBase": "from sqlalchemy.orm import DeclarativeBase",
    "Mapped": "from sqlalchemy.orm import Mapped",
    "mapped_column": "from sqlalchemy.orm import mapped_column",
    "relationship": "from sqlalchemy.orm import relationship",
    "select": "from sqlalchemy import select",
    "func": "from sqlalchemy import func",
}

# Pydantic v1 to v2 replacements
PYDANTIC_V2_FIXES = [
    # Import changes
    (r"from pydantic import BaseSettings", "from pydantic_settings import BaseSettings"),
    (r"from pydantic import (.*?)BaseSettings(.*?)", r"from pydantic import \1\2\nfrom pydantic_settings import BaseSettings"),

    # Config class to model_config
    (r"class Config:\s*\n\s*orm_mode\s*=\s*True", "model_config = ConfigDict(from_attributes=True)"),
    (r"class Config:\s*\n\s*env_file\s*=\s*['\"](.+?)['\"]",
     r'model_config = ConfigDict(env_file="\1")'),

    # orm_mode to from_attributes
    (r"orm_mode\s*=\s*True", "from_attributes=True"),
]


class CodePostProcessor:
    """Post-processes generated Python code to fix common issues."""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.fixes_applied = []

    def process_all_files(self) -> dict:
        """Process all Python files in the project."""
        results = {
            "processed": 0,
            "fixed": 0,
            "errors": [],
            "files": [],
        }

        for py_file in self.project_dir.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                file_result = self.process_file(py_file)
                results["processed"] += 1
                if file_result["changes_made"]:
                    results["fixed"] += 1
                    results["files"].append({
                        "path": str(py_file.relative_to(self.project_dir)),
                        "fixes": file_result["fixes"],
                    })
            except Exception as e:
                results["errors"].append({
                    "path": str(py_file),
                    "error": str(e),
                })
                logger.error(f"Error processing {py_file}: {e}")

        return results

    def process_file(self, file_path: Path) -> dict:
        """Process a single Python file."""
        content = file_path.read_text(encoding="utf-8")
        original_content = content
        fixes = []

        # 1. Fix Pydantic v1 → v2 syntax
        content, pydantic_fixes = self._fix_pydantic_v2(content)
        fixes.extend(pydantic_fixes)

        # 2. Add missing imports
        content, import_fixes = self._add_missing_imports(content)
        fixes.extend(import_fixes)

        # 3. Fix common syntax issues
        content, syntax_fixes = self._fix_common_syntax(content)
        fixes.extend(syntax_fixes)

        # 4. Validate syntax
        is_valid, error = self._validate_syntax(content)
        if not is_valid:
            logger.warning(f"Syntax still invalid after fixes: {file_path}: {error}")

        # Write if changed
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"Fixed {file_path}", fixes=len(fixes))

        return {
            "changes_made": content != original_content,
            "fixes": fixes,
            "valid_syntax": is_valid,
        }

    def _fix_pydantic_v2(self, content: str) -> tuple[str, list]:
        """Apply Pydantic v1 to v2 fixes."""
        fixes = []

        for pattern, replacement in PYDANTIC_V2_FIXES:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                fixes.append(f"Pydantic v2: {pattern[:30]}...")

        # Ensure ConfigDict is imported if used
        if "ConfigDict" in content and "from pydantic import" in content:
            if "ConfigDict" not in content.split("from pydantic import")[1].split("\n")[0]:
                content = re.sub(
                    r"(from pydantic import .+?)(\n|$)",
                    r"\1, ConfigDict\2",
                    content,
                    count=1
                )
                fixes.append("Added ConfigDict to pydantic imports")

        return content, fixes

    def _add_missing_imports(self, content: str) -> tuple[str, list]:
        """Add missing imports based on usage analysis."""
        fixes = []
        lines = content.split("\n")

        # Find existing imports
        existing_imports = set()
        import_end_line = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_end_line = i
                # Extract imported names
                if "import" in line:
                    parts = line.split("import")[-1]
                    for name in parts.split(","):
                        name = name.strip().split(" as ")[0].strip()
                        if name:
                            existing_imports.add(name)

        # Find used names that need imports
        needed_imports = []
        code_section = "\n".join(lines[import_end_line + 1:])

        for name, import_stmt in IMPORT_MAPPINGS.items():
            if name not in existing_imports:
                # Check if name is used in code (not in strings or comments)
                pattern = rf'\b{re.escape(name)}\b'
                # Simple check - could be improved with AST
                if re.search(pattern, code_section):
                    needed_imports.append(import_stmt)
                    fixes.append(f"Added import: {name}")

        # Add imports after existing imports
        if needed_imports:
            # Remove duplicates while preserving order
            seen = set()
            unique_imports = []
            for imp in needed_imports:
                if imp not in seen:
                    seen.add(imp)
                    unique_imports.append(imp)

            # Insert imports
            import_block = "\n".join(unique_imports)
            lines.insert(import_end_line + 1, import_block)
            content = "\n".join(lines)

        return content, fixes

    def _fix_common_syntax(self, content: str) -> tuple[str, list]:
        """Fix common syntax issues."""
        fixes = []

        # Fix trailing commas in function definitions that cause issues
        # This is a simple fix - more complex ones would need AST

        # Fix empty __init__.py that should have pass or docstring
        if content.strip() == "" or content.strip() == '"""Generated by Sovereign AI"""':
            content = '"""Generated by Sovereign AI."""\n'

        return content, fixes

    def _validate_syntax(self, content: str) -> tuple[bool, Optional[str]]:
        """Validate Python syntax using AST."""
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"

    def run_linter(self) -> dict:
        """Run ruff linter on the project."""
        try:
            result = subprocess.run(
                ["ruff", "check", str(self.project_dir), "--fix"],
                capture_output=True,
                text=True,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "ruff not installed",
            }


def post_process_project(project_dir: str) -> dict:
    """
    Post-process a generated project to fix common issues.

    Args:
        project_dir: Path to the generated project

    Returns:
        Dictionary with processing results
    """
    processor = CodePostProcessor(Path(project_dir))
    results = processor.process_all_files()

    logger.info(
        "Post-processing complete",
        processed=results["processed"],
        fixed=results["fixed"],
        errors=len(results["errors"]),
    )

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python post_processor.py <project_dir>")
        sys.exit(1)

    results = post_process_project(sys.argv[1])
    print(f"Processed: {results['processed']} files")
    print(f"Fixed: {results['fixed']} files")
    if results['errors']:
        print(f"Errors: {len(results['errors'])}")
        for err in results['errors']:
            print(f"  - {err['path']}: {err['error']}")
