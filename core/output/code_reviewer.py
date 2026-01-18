"""
Code Reviewer Agent
==================
Reviews generated code and fixes issues:
- Missing imports
- Type mismatches
- Consistency across files
- Best practice violations
"""

import re
from typing import Optional

import structlog

logger = structlog.get_logger()


# Common issues and their fixes
REVIEW_RULES = [
    {
        "name": "missing_decimal_import",
        "pattern": r"\bDecimal\b",
        "check_import": "from decimal import Decimal",
        "fix": "from decimal import Decimal",
        "description": "Decimal used without import",
    },
    {
        "name": "missing_optional_import",
        "pattern": r"\bOptional\[",
        "check_import": "from typing import Optional",
        "fix": "from typing import Optional",
        "description": "Optional used without import",
    },
    {
        "name": "missing_uuid_import",
        "pattern": r"\bUUID\b",
        "check_import": "from uuid import UUID",
        "fix": "from uuid import UUID",
        "description": "UUID used without import",
    },
    {
        "name": "missing_datetime_import",
        "pattern": r"\bdatetime\b",
        "check_import": "from datetime import datetime",
        "fix": "from datetime import datetime",
        "description": "datetime used without import",
    },
    {
        "name": "missing_configdict_import",
        "pattern": r"\bConfigDict\b",
        "check_import": "from pydantic import ConfigDict",
        "fix": "from pydantic import ConfigDict",
        "description": "ConfigDict used without import",
    },
    {
        "name": "pydantic_v1_basesettings",
        "pattern": r"from pydantic import.*BaseSettings",
        "fix_pattern": (r"from pydantic import (.*?)BaseSettings(.*)",
                        r"from pydantic import \1\2\nfrom pydantic_settings import BaseSettings"),
        "description": "BaseSettings should be from pydantic_settings in v2",
    },
    {
        "name": "missing_field_import",
        "pattern": r"\bField\(",
        "check_import": "from pydantic import Field",
        "fix": "from pydantic import Field",
        "description": "Field used without import",
    },
]


class CodeReviewer:
    """Reviews and fixes code issues."""

    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []

    def review_code(self, code: str, filename: str = "unknown") -> dict:
        """
        Review code and identify issues.

        Returns dict with:
        - issues: list of identified issues
        - suggestions: list of fix suggestions
        - fixed_code: code with auto-fixable issues resolved
        """
        issues = []
        suggestions = []
        fixed_code = code

        for rule in REVIEW_RULES:
            if re.search(rule["pattern"], code):
                # Check if the required import exists
                check_import = rule.get("check_import", "")
                if check_import and check_import not in code:
                    issues.append({
                        "rule": rule["name"],
                        "description": rule["description"],
                        "file": filename,
                    })

                    # Apply fix if available
                    if "fix" in rule:
                        suggestions.append(f"Add: {rule['fix']}")
                        # Add import at the top
                        if rule["fix"] not in fixed_code:
                            fixed_code = self._add_import(fixed_code, rule["fix"])
                            self.fixes_applied.append(rule["name"])

                    elif "fix_pattern" in rule:
                        pattern, replacement = rule["fix_pattern"]
                        if re.search(pattern, fixed_code):
                            fixed_code = re.sub(pattern, replacement, fixed_code)
                            self.fixes_applied.append(rule["name"])

        return {
            "issues": issues,
            "suggestions": suggestions,
            "fixed_code": fixed_code,
            "has_issues": len(issues) > 0,
        }

    def _add_import(self, code: str, import_stmt: str) -> str:
        """Add an import statement to code."""
        lines = code.split("\n")

        # Find the last import line
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import_idx = i

        # Insert after last import
        lines.insert(last_import_idx + 1, import_stmt)
        return "\n".join(lines)

    def review_project(self, files: dict[str, str]) -> dict:
        """
        Review entire project for cross-file consistency.

        Args:
            files: dict mapping filepath to content

        Returns:
            Review results with issues and fixes
        """
        all_issues = []
        fixed_files = {}
        cross_file_issues = []

        # First pass: individual file review
        for filepath, content in files.items():
            if filepath.endswith(".py"):
                result = self.review_code(content, filepath)
                fixed_files[filepath] = result["fixed_code"]
                all_issues.extend(result["issues"])

        # Second pass: cross-file consistency
        # Check for naming consistency
        defined_names = self._extract_defined_names(fixed_files)
        used_names = self._extract_used_names(fixed_files)

        for name, used_in in used_names.items():
            if name not in defined_names and not self._is_external(name):
                cross_file_issues.append({
                    "type": "undefined_reference",
                    "name": name,
                    "used_in": used_in,
                    "suggestion": f"'{name}' is used but not defined in project",
                })

        return {
            "individual_issues": all_issues,
            "cross_file_issues": cross_file_issues,
            "fixed_files": fixed_files,
            "total_issues": len(all_issues) + len(cross_file_issues),
            "fixes_applied": self.fixes_applied,
        }

    def _extract_defined_names(self, files: dict[str, str]) -> set:
        """Extract class and function names defined in files."""
        names = set()
        for content in files.values():
            # Classes
            names.update(re.findall(r"class\s+(\w+)", content))
            # Functions
            names.update(re.findall(r"def\s+(\w+)", content))
            # Variables at module level
            names.update(re.findall(r"^(\w+)\s*=", content, re.MULTILINE))
        return names

    def _extract_used_names(self, files: dict[str, str]) -> dict:
        """Extract names used across files with their locations."""
        used = {}
        for filepath, content in files.items():
            # Look for imports from app.* modules
            imports = re.findall(r"from app\.\w+(?:\.\w+)* import (.+)", content)
            for imp in imports:
                for name in imp.split(","):
                    name = name.strip().split(" as ")[0].strip()
                    if name:
                        if name not in used:
                            used[name] = []
                        used[name].append(filepath)
        return used

    def _is_external(self, name: str) -> bool:
        """Check if a name is from an external package."""
        external_names = {
            # FastAPI
            "FastAPI", "APIRouter", "Depends", "HTTPException", "Query",
            "Header", "Request", "Response", "status",
            # Pydantic
            "BaseModel", "Field", "ConfigDict", "BaseSettings",
            # SQLAlchemy
            "AsyncSession", "select", "func", "Mapped", "mapped_column",
            "DeclarativeBase", "relationship",
            # Standard library
            "Optional", "List", "Dict", "Any", "Union",
            "datetime", "Decimal", "UUID",
        }
        return name in external_names


def create_review_prompt(code: str, issues: list) -> str:
    """
    Create a prompt for the LLM to review and fix code.

    This can be used in a multi-pass generation pipeline.
    """
    issues_text = "\n".join([f"- {i['description']}" for i in issues])

    prompt = f"""Review and fix the following code issues:

ISSUES FOUND:
{issues_text}

CODE TO FIX:
```python
{code}
```

Please provide the corrected code with all issues fixed.
Ensure all imports are present at the top of the file.
Use Pydantic v2 syntax (pydantic_settings for BaseSettings, ConfigDict instead of class Config).
"""
    return prompt
