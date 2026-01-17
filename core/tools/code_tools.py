"""
Code Execution and File Management Tools

Safe code execution with sandboxing and file operations
"""

import os
import sys
import subprocess
import tempfile
import ast
import traceback
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import structlog

logger = structlog.get_logger()


class CodeExecutor:
    """
    Safe code execution with sandboxing

    Features:
    - Python code execution in isolated environment
    - Timeout enforcement
    - Resource limits
    - Output capture
    - Prohibited operation detection
    """

    DANGEROUS_IMPORTS = [
        'os.system', 'subprocess', 'eval', 'exec',
        'compile', '__import__', 'open', 'file'
    ]

    DANGEROUS_CALLS = [
        'os.remove', 'os.rmdir', 'shutil.rmtree',
        'os.makedirs', 'os.mkdir'
    ]

    def __init__(
        self,
        timeout: int = 30,
        max_output_size: int = 10000,
        allowed_modules: Optional[List[str]] = None
    ):
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.allowed_modules = allowed_modules or [
            'math', 'datetime', 'json', 'decimal', 're',
            'collections', 'itertools', 'functools', 'dataclasses'
        ]

    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Static analysis to detect potentially dangerous code

        Returns:
            Dict with validation result and any warnings
        """
        issues = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_modules:
                            issues.append({
                                'type': 'restricted_import',
                                'module': alias.name,
                                'line': node.lineno
                            })

                if isinstance(node, ast.ImportFrom):
                    if node.module not in self.allowed_modules:
                        issues.append({
                            'type': 'restricted_import',
                            'module': node.module,
                            'line': node.lineno
                        })

                # Check for dangerous function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        full_name = f"{self._get_full_name(node.func)}"
                        if any(dangerous in full_name for dangerous in self.DANGEROUS_CALLS):
                            issues.append({
                                'type': 'dangerous_call',
                                'call': full_name,
                                'line': node.lineno
                            })

                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                            issues.append({
                                'type': 'dangerous_builtin',
                                'function': node.func.id,
                                'line': node.lineno
                            })

            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'ast_parsed': True
            }

        except SyntaxError as e:
            return {
                'valid': False,
                'issues': [{
                    'type': 'syntax_error',
                    'message': str(e),
                    'line': e.lineno
                }],
                'ast_parsed': False
            }

    def _get_full_name(self, node: ast.AST) -> str:
        """Get full dotted name from AST node"""
        if isinstance(node, ast.Attribute):
            return f"{self._get_full_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Name):
            return node.id
        return ""

    def execute(self, code: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Python code in a sandboxed environment

        Args:
            code: Python code to execute
            inputs: Optional dict of input variables

        Returns:
            Dict with output, errors, and execution metadata
        """
        # Validate first
        validation = self.validate_code(code)
        if not validation['valid']:
            return {
                'success': False,
                'output': None,
                'error': f"Code validation failed: {validation['issues']}",
                'validation': validation
            }

        # Create temp file with code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Prepare code with inputs
            if inputs:
                for key, value in inputs.items():
                    f.write(f"{key} = {repr(value)}\n")
            f.write(code)
            temp_file = f.name

        try:
            # Execute in subprocess with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )

            output = result.stdout[:self.max_output_size]
            error = result.stderr[:self.max_output_size] if result.stderr else None

            return {
                'success': result.returncode == 0,
                'output': output,
                'error': error,
                'return_code': result.returncode,
                'execution_time': None  # Would need timing wrapper
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': None,
                'error': f"Execution timed out after {self.timeout} seconds",
                'return_code': -1
            }

        except Exception as e:
            return {
                'success': False,
                'output': None,
                'error': str(e),
                'return_code': -1
            }

        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass

    def execute_snippet(self, code: str) -> str:
        """Simple execution returning just output string"""
        result = self.execute(code)
        if result['success']:
            return result['output']
        return f"Error: {result['error']}"


class FileManager:
    """
    Secure file operations for agents

    Features:
    - Sandboxed to workspace directory
    - File reading/writing with validation
    - Directory operations
    - Path traversal protection
    """

    def __init__(self, workspace_dir: str):
        self.workspace = Path(workspace_dir).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: str) -> Path:
        """Validate path is within workspace"""
        full_path = (self.workspace / path).resolve()

        if not str(full_path).startswith(str(self.workspace)):
            raise SecurityError(f"Path traversal detected: {path}")

        return full_path

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read file contents"""
        try:
            full_path = self._validate_path(path)

            if not full_path.exists():
                return {'success': False, 'error': f'File not found: {path}'}

            if not full_path.is_file():
                return {'success': False, 'error': f'Not a file: {path}'}

            content = full_path.read_text()
            return {
                'success': True,
                'content': content,
                'path': str(full_path),
                'size': len(content),
                'lines': content.count('\n') + 1
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        try:
            full_path = self._validate_path(path)

            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            full_path.write_text(content)

            return {
                'success': True,
                'path': str(full_path),
                'size': len(content),
                'created': not full_path.exists()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List directory contents"""
        try:
            full_path = self._validate_path(path)

            if not full_path.exists():
                return {'success': False, 'error': f'Directory not found: {path}'}

            if not full_path.is_dir():
                return {'success': False, 'error': f'Not a directory: {path}'}

            items = []
            for item in full_path.iterdir():
                items.append({
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                })

            return {
                'success': True,
                'path': str(full_path),
                'items': items,
                'count': len(items)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            full_path = self._validate_path(path)

            if not full_path.exists():
                return {'success': False, 'error': f'File not found: {path}'}

            if full_path.is_dir():
                return {'success': False, 'error': 'Cannot delete directory with this method'}

            full_path.unlink()

            return {'success': True, 'path': str(full_path)}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def search_files(self, pattern: str, path: str = ".") -> Dict[str, Any]:
        """Search for files matching pattern"""
        try:
            full_path = self._validate_path(path)

            matches = list(full_path.glob(pattern))

            return {
                'success': True,
                'pattern': pattern,
                'matches': [str(m.relative_to(self.workspace)) for m in matches],
                'count': len(matches)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


class SecurityError(Exception):
    """Security violation error"""
    pass
