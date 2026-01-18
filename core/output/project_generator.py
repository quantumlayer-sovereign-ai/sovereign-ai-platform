"""
Project Generator

Generates enterprise folder structures from agent outputs:
- Extracts code blocks from markdown
- Organizes into proper folder structure
- Generates README and requirements.txt
- Saves to disk for later retrieval/download
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from .models import CodeBlock, ProjectFile, ProjectManifest

logger = structlog.get_logger()


class ProjectGenerator:
    """Generate enterprise folder structure from agent outputs"""

    # Language to file extension mapping
    LANG_EXTENSIONS = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "java": ".java",
        "go": ".go",
        "rust": ".rs",
        "c": ".c",
        "cpp": ".cpp",
        "csharp": ".cs",
        "ruby": ".rb",
        "php": ".php",
        "swift": ".swift",
        "kotlin": ".kt",
        "scala": ".scala",
        "bash": ".sh",
        "shell": ".sh",
        "sql": ".sql",
        "html": ".html",
        "css": ".css",
        "json": ".json",
        "yaml": ".yaml",
        "yml": ".yml",
        "xml": ".xml",
        "markdown": ".md",
        "dockerfile": "",  # No extension for Dockerfile
        "env": "",  # .env files
        "txt": ".txt",
        "text": ".txt",
        "toml": ".toml",
        "ini": ".ini",
    }

    # Files that should go at project root
    ROOT_FILES = {
        '.env', '.env.example', '.env.sample',
        'requirements.txt', 'setup.py', 'pyproject.toml',
        'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
        '.gitignore', 'Makefile', 'README.md',
    }

    # Keywords that suggest test files
    TEST_KEYWORDS = ["test_", "_test", "test", "spec", "_spec"]

    def __init__(self, base_dir: str = "projects"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def generate(
        self,
        task_id: str,
        results: list[dict[str, Any]],
        task: str,
        agents_used: list[str] | None = None,
    ) -> ProjectManifest:
        """
        Extract code from agent results and create project structure.

        Args:
            task_id: Unique task identifier
            results: List of agent result dicts with 'response' key
            task: Original task description
            agents_used: List of agent names that contributed

        Returns:
            ProjectManifest with project metadata

        Creates structure:
        projects/{task_id}/
        ├── manifest.json          # Project metadata
        ├── README.md              # Auto-generated docs
        ├── src/
        │   ├── __init__.py
        │   └── {module_name}.py   # Main code files
        ├── tests/
        │   └── test_{module}.py   # Test files
        └── requirements.txt       # Dependencies
        """
        agents_used = agents_used or []

        # Extract code blocks from all results
        code_blocks = self._extract_code_blocks(results)
        logger.info(
            "code_blocks_extracted",
            task_id=task_id,
            count=len(code_blocks),
        )

        # Determine file structure based on code and task
        file_structure = self._determine_file_structure(code_blocks, task)

        # Generate project files
        project_files: list[ProjectFile] = []

        # Add source files
        for path, content in file_structure.get("src", {}).items():
            lang = self._detect_language(path)
            project_files.append(ProjectFile(path=path, content=content, language=lang))

        # Add test files
        for path, content in file_structure.get("tests", {}).items():
            lang = self._detect_language(path)
            project_files.append(ProjectFile(path=path, content=content, language=lang))

        # Add root files (like .env, requirements.txt from output)
        for path, content in file_structure.get("root", {}).items():
            lang = self._detect_language(path)
            project_files.append(ProjectFile(path=path, content=content, language=lang))

        # Generate README
        readme_content = self._generate_readme(task, code_blocks, agents_used)
        project_files.append(
            ProjectFile(path="README.md", content=readme_content, language="markdown")
        )

        # Generate requirements.txt for Python projects (only if not already in root files)
        if not any(f.path == "requirements.txt" for f in project_files):
            dependencies = self._extract_dependencies(code_blocks)
            if dependencies:
                req_content = "\n".join(sorted(dependencies)) + "\n"
                project_files.append(
                    ProjectFile(path="requirements.txt", content=req_content, language="text")
                )

        # Add __init__.py for all Python packages (nested directories)
        if any(f.path.endswith(".py") for f in project_files):
            # Collect all directories that contain .py files
            py_dirs: set[str] = set()
            for f in project_files:
                if f.path.endswith(".py"):
                    parts = Path(f.path).parts
                    # Add all parent directories
                    for i in range(1, len(parts)):
                        dir_path = "/".join(parts[:i])
                        py_dirs.add(dir_path)

            # Add __init__.py for each directory
            for dir_path in sorted(py_dirs):
                init_path = f"{dir_path}/__init__.py"
                if not any(f.path == init_path for f in project_files):
                    project_files.append(
                        ProjectFile(
                            path=init_path,
                            content=f'"""Generated by Sovereign AI - {dir_path} package"""\n',
                            language="python"
                        )
                    )

        # Create manifest
        manifest = ProjectManifest(
            task_id=task_id,
            task=task,
            created_at=datetime.now(),
            files=project_files,
            agents_used=agents_used,
        )

        # Save to disk
        await self._save_project(manifest)

        logger.info(
            "project_generated",
            task_id=task_id,
            files=manifest.total_files,
            size=manifest.total_size,
        )

        return manifest

    def _extract_code_blocks(self, results: list[dict[str, Any]]) -> list[CodeBlock]:
        """Extract all code blocks from agent results"""
        code_blocks: list[CodeBlock] = []

        # Regex to match markdown code blocks with optional preceding path
        # Matches: #### `app/config/settings.py` or #### app/config/settings.py
        # Followed by: ```language\ncode\n```
        path_code_pattern = re.compile(
            r'(?:#{1,4}\s*`?([a-zA-Z0-9_/.-]+\.\w+)`?\s*\n)?```(\w+)?\s*\n(.*?)```',
            re.DOTALL
        )

        for result in results:
            response = result.get("response", "")
            agent = result.get("agent", result.get("role", "unknown"))

            # Find all code blocks in the response
            matches = path_code_pattern.findall(response)

            for filepath, lang, content in matches:
                lang = lang.strip() if lang else "text"
                content = content.strip()

                if not content:
                    continue

                # Use explicit filepath if found, otherwise extract from code
                if filepath and '/' in filepath:
                    suggested_filename = filepath.strip('`').strip()
                else:
                    suggested_filename = self._extract_filename_from_code(content, lang)

                code_blocks.append(
                    CodeBlock(
                        content=content,
                        language=lang,
                        agent=agent,
                        suggested_filename=suggested_filename,
                    )
                )

        return code_blocks

    def _extract_filename_from_code(self, content: str, language: str) -> str:
        """Extract filename from code comments or generate one"""
        lines = content.split("\n")

        # Look for filename in first few lines
        # Patterns: # filename.py, // filename.js, /* filename.java */
        # Also handles paths like: # app/models/user.py
        filename_patterns = [
            r'^#\s*(?:file(?:name)?:?\s*)?([a-zA-Z0-9_/.-]+\.\w+)',      # Python/Bash: # app/models/user.py
            r'^//\s*(?:file(?:name)?:?\s*)?([a-zA-Z0-9_/.-]+\.\w+)',     # JS/TS/Go: // filename.js
            r'^/\*\s*(?:file(?:name)?:?\s*)?([a-zA-Z0-9_/.-]+\.\w+)',    # Java/C: /* filename.java
        ]

        for line in lines[:5]:  # Check first 5 lines
            for pattern in filename_patterns:
                match = re.match(pattern, line.strip(), re.IGNORECASE)
                if match:
                    return match.group(1)

        # Try to extract class/function name for generating filename
        class_match = re.search(r'class\s+(\w+)', content)
        if class_match:
            name = self._to_snake_case(class_match.group(1))
            ext = self.LANG_EXTENSIONS.get(language, ".txt")
            return f"{name}{ext}"

        func_match = re.search(r'(?:def|function|func|fn)\s+(\w+)', content)
        if func_match:
            name = self._to_snake_case(func_match.group(1))
            ext = self.LANG_EXTENSIONS.get(language, ".txt")
            return f"{name}{ext}"

        # Check for FastAPI router decorators
        router_match = re.search(r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)', content)
        if router_match:
            endpoint = router_match.group(2).strip('/').replace('/', '_').replace('-', '_')
            if endpoint:
                ext = self.LANG_EXTENSIONS.get(language, ".txt")
                return f"{endpoint}_router{ext}"

        # Default filename
        ext = self.LANG_EXTENSIONS.get(language, ".txt")
        return f"main{ext}"

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _determine_file_structure(
        self,
        code_blocks: list[CodeBlock],
        task: str,
    ) -> dict[str, dict[str, str]]:
        """Determine file structure based on code blocks and task"""
        structure: dict[str, dict[str, str]] = {
            "src": {},
            "tests": {},
            "root": {},  # Files at project root
        }

        # Track used filenames to avoid conflicts
        used_paths: set[str] = set()

        for block in code_blocks:
            filename = block.suggested_filename

            # Check if filename already has a proper path structure (e.g., app/models/user.py)
            has_path_structure = '/' in filename and not filename.startswith('src/')

            # Check if it's a test file
            is_test = any(kw in filename.lower() for kw in self.TEST_KEYWORDS)

            # Check if it's a config/env file that should be at root
            base_filename = Path(filename).name
            is_root_file = base_filename in self.ROOT_FILES or filename in self.ROOT_FILES

            if has_path_structure:
                # Preserve the existing path structure
                path = filename
                # Ensure unique path
                counter = 1
                base_path = path
                while path in used_paths:
                    stem = Path(base_path).stem
                    ext = Path(base_path).suffix
                    parent = str(Path(base_path).parent)
                    path = f"{parent}/{stem}_{counter}{ext}"
                    counter += 1
                used_paths.add(path)
                structure["src"][path] = block.content
            elif is_root_file:
                structure["root"][filename] = block.content
            elif is_test:
                base_name = Path(filename).stem
                ext = Path(filename).suffix or self.LANG_EXTENSIONS.get(block.language, ".txt")
                final_name = f"{base_name}{ext}"
                counter = 1
                while f"tests/{final_name}" in used_paths:
                    final_name = f"{base_name}_{counter}{ext}"
                    counter += 1
                path = f"tests/{final_name}"
                used_paths.add(path)
                structure["tests"][path] = block.content
            else:
                base_name = Path(filename).stem
                ext = Path(filename).suffix or self.LANG_EXTENSIONS.get(block.language, ".txt")
                final_name = f"{base_name}{ext}"
                counter = 1
                while f"src/{final_name}" in used_paths:
                    final_name = f"{base_name}_{counter}{ext}"
                    counter += 1
                path = f"src/{final_name}"
                used_paths.add(path)
                structure["src"][path] = block.content

        return structure

    def _detect_language(self, path: str) -> str:
        """Detect language from file path"""
        ext = Path(path).suffix.lower()
        ext_to_lang = {v: k for k, v in self.LANG_EXTENSIONS.items()}
        return ext_to_lang.get(ext, "text")

    def _generate_readme(
        self,
        task: str,
        code_blocks: list[CodeBlock],
        agents_used: list[str],
    ) -> str:
        """Generate README.md content"""
        # Extract languages used
        languages = list(set(b.language for b in code_blocks))

        # Count files by type
        src_count = sum(1 for b in code_blocks if not any(kw in b.suggested_filename.lower() for kw in self.TEST_KEYWORDS))
        test_count = len(code_blocks) - src_count

        readme = f"""# Generated Project

> Generated by Sovereign AI Platform

## Task

{task}

## Project Structure

```
├── README.md
├── requirements.txt
├── src/           # Source files ({src_count} files)
└── tests/         # Test files ({test_count} files)
```

## Languages

{', '.join(languages) if languages else 'N/A'}

## Agents Used

{chr(10).join(f'- {agent}' for agent in agents_used) if agents_used else '- N/A'}

## Getting Started

```bash
# Install dependencies (Python)
pip install -r requirements.txt

# Run tests
pytest tests/
```

## Generated At

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*This project was automatically generated by the Sovereign AI Platform.*
"""
        return readme

    def _extract_dependencies(self, code_blocks: list[CodeBlock]) -> list[str]:
        """Extract Python dependencies from import statements"""
        dependencies: set[str] = set()

        # Common standard library modules to exclude
        stdlib = {
            "os", "sys", "re", "json", "datetime", "time", "math", "random",
            "collections", "itertools", "functools", "pathlib", "typing",
            "dataclasses", "enum", "abc", "io", "asyncio", "concurrent",
            "threading", "multiprocessing", "subprocess", "socket", "http",
            "urllib", "email", "html", "xml", "logging", "warnings",
            "contextlib", "copy", "pickle", "hashlib", "secrets", "base64",
            "uuid", "tempfile", "shutil", "glob", "fnmatch", "stat",
        }

        # Known package mappings
        package_map = {
            "cv2": "opencv-python",
            "sklearn": "scikit-learn",
            "PIL": "Pillow",
            "yaml": "pyyaml",
            "bs4": "beautifulsoup4",
            "dotenv": "python-dotenv",
        }

        for block in code_blocks:
            if block.language != "python":
                continue

            # Find import statements
            import_patterns = [
                r'^import\s+(\w+)',           # import module
                r'^from\s+(\w+)',             # from module import ...
            ]

            for line in block.content.split("\n"):
                line = line.strip()
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        module = match.group(1)
                        if module not in stdlib:
                            # Map to package name if known
                            package = package_map.get(module, module)
                            dependencies.add(package)

        return list(dependencies)

    async def _save_project(self, manifest: ProjectManifest) -> None:
        """Save project to disk"""
        project_dir = self.base_dir / manifest.task_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # Save each file
        for file in manifest.files:
            file_path = project_dir / file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file.content, encoding="utf-8")

        # Save manifest (without file contents for quick loading)
        manifest_data = manifest.to_dict()
        # Remove content from files for manifest.json (content is in the actual files)
        for f in manifest_data["files"]:
            f.pop("content", None)

        manifest_path = project_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        logger.info(
            "project_saved",
            task_id=manifest.task_id,
            path=str(project_dir),
        )

    async def get_project(self, task_id: str) -> ProjectManifest | None:
        """Load project manifest from disk"""
        project_dir = self.base_dir / task_id
        manifest_path = project_dir / "manifest.json"

        if not manifest_path.exists():
            return None

        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

        # Load file contents
        files: list[ProjectFile] = []
        for file_info in manifest_data.get("files", []):
            file_path = project_dir / file_info["path"]
            content = ""
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
            files.append(
                ProjectFile(
                    path=file_info["path"],
                    content=content,
                    language=file_info["language"],
                )
            )

        return ProjectManifest(
            task_id=manifest_data["task_id"],
            task=manifest_data["task"],
            created_at=datetime.fromisoformat(manifest_data["created_at"]),
            files=files,
            agents_used=manifest_data.get("agents_used", []),
        )

    async def get_file(self, task_id: str, path: str) -> ProjectFile | None:
        """Load a single file from a project"""
        project_dir = self.base_dir / task_id
        file_path = project_dir / path

        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        language = self._detect_language(path)

        return ProjectFile(path=path, content=content, language=language)

    def list_projects(self) -> list[dict[str, Any]]:
        """List all projects"""
        projects = []

        for project_dir in self.base_dir.iterdir():
            if not project_dir.is_dir():
                continue

            manifest_path = project_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    data = json.loads(manifest_path.read_text(encoding="utf-8"))
                    projects.append({
                        "task_id": data["task_id"],
                        "task": data["task"],
                        "created_at": data["created_at"],
                        "total_files": data.get("total_files", 0),
                        "total_size": data.get("total_size", 0),
                    })
                except Exception as e:
                    logger.warning("failed_to_load_manifest", path=str(manifest_path), error=str(e))

        # Sort by created_at descending
        projects.sort(key=lambda p: p["created_at"], reverse=True)
        return projects
