"""
Git Operations Tools

Safe git operations for code management
"""

import os
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import structlog

logger = structlog.get_logger()


class GitOperations:
    """
    Git operations for AI agents

    Features:
    - Repository initialization
    - Commit and branch operations
    - Diff and log viewing
    - Safe merge operations
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self._ensure_repo()

    def _ensure_repo(self):
        """Ensure repository exists or initialize"""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            self.init()

    def _run_git(self, *args, check: bool = True) -> Dict[str, Any]:
        """Run a git command"""
        cmd = ["git"] + list(args)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            if check and result.returncode != 0:
                return {
                    'success': False,
                    'error': result.stderr,
                    'command': ' '.join(cmd)
                }

            return {
                'success': True,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Git command timed out',
                'command': ' '.join(cmd)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': ' '.join(cmd)
            }

    def init(self, bare: bool = False) -> Dict[str, Any]:
        """Initialize a new repository"""
        self.repo_path.mkdir(parents=True, exist_ok=True)
        args = ["init"]
        if bare:
            args.append("--bare")
        return self._run_git(*args)

    def status(self) -> Dict[str, Any]:
        """Get repository status"""
        result = self._run_git("status", "--porcelain", "-b")

        if not result['success']:
            return result

        lines = result['output'].strip().split('\n') if result['output'].strip() else []

        # Parse status
        branch_line = lines[0] if lines and lines[0].startswith('##') else None
        file_lines = [l for l in lines if not l.startswith('##')]

        staged = []
        modified = []
        untracked = []

        for line in file_lines:
            if not line:
                continue
            status_code = line[:2]
            filename = line[3:]

            if status_code[0] in 'MADRC':
                staged.append({'file': filename, 'status': status_code[0]})
            if status_code[1] in 'MADRC':
                modified.append({'file': filename, 'status': status_code[1]})
            if status_code == '??':
                untracked.append(filename)

        return {
            'success': True,
            'branch': branch_line[3:].split('...')[0] if branch_line else 'unknown',
            'staged': staged,
            'modified': modified,
            'untracked': untracked,
            'clean': len(staged) == 0 and len(modified) == 0 and len(untracked) == 0
        }

    def add(self, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Stage files for commit"""
        if files is None:
            return self._run_git("add", "-A")
        return self._run_git("add", *files)

    def commit(self, message: str, author: Optional[str] = None) -> Dict[str, Any]:
        """Create a commit"""
        args = ["commit", "-m", message]
        if author:
            args.extend(["--author", author])

        result = self._run_git(*args)

        if result['success']:
            # Get commit hash
            hash_result = self._run_git("rev-parse", "HEAD")
            if hash_result['success']:
                result['commit_hash'] = hash_result['output'].strip()

        return result

    def log(self, count: int = 10, format_str: Optional[str] = None) -> Dict[str, Any]:
        """Get commit log"""
        format_str = format_str or "%H|%an|%ae|%at|%s"
        result = self._run_git("log", f"-{count}", f"--format={format_str}")

        if not result['success']:
            return result

        commits = []
        for line in result['output'].strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 5:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'timestamp': int(parts[3]),
                    'message': parts[4]
                })

        return {
            'success': True,
            'commits': commits,
            'count': len(commits)
        }

    def diff(self, staged: bool = False, file: Optional[str] = None) -> Dict[str, Any]:
        """Get diff"""
        args = ["diff"]
        if staged:
            args.append("--staged")
        if file:
            args.extend(["--", file])

        result = self._run_git(*args)

        if result['success']:
            result['lines_added'] = result['output'].count('\n+') if result['output'] else 0
            result['lines_removed'] = result['output'].count('\n-') if result['output'] else 0

        return result

    def branch(self, name: Optional[str] = None, delete: bool = False) -> Dict[str, Any]:
        """Create, delete, or list branches"""
        if name is None:
            # List branches
            result = self._run_git("branch", "-a")
            if result['success']:
                branches = [b.strip().lstrip('* ') for b in result['output'].split('\n') if b.strip()]
                current = None
                for b in result['output'].split('\n'):
                    if b.strip().startswith('*'):
                        current = b.strip()[2:]
                        break
                result['branches'] = branches
                result['current'] = current
            return result

        if delete:
            return self._run_git("branch", "-D", name)

        return self._run_git("branch", name)

    def checkout(self, target: str, create: bool = False) -> Dict[str, Any]:
        """Checkout branch or commit"""
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(target)
        return self._run_git(*args)

    def merge(self, branch: str, no_ff: bool = False) -> Dict[str, Any]:
        """Merge a branch"""
        args = ["merge"]
        if no_ff:
            args.append("--no-ff")
        args.append(branch)
        return self._run_git(*args)

    def reset(self, mode: str = "mixed", target: str = "HEAD") -> Dict[str, Any]:
        """Reset to a target"""
        if mode not in ["soft", "mixed", "hard"]:
            return {'success': False, 'error': f'Invalid reset mode: {mode}'}

        return self._run_git("reset", f"--{mode}", target)

    def stash(self, pop: bool = False, message: Optional[str] = None) -> Dict[str, Any]:
        """Stash or unstash changes"""
        if pop:
            return self._run_git("stash", "pop")

        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])

        return self._run_git(*args)

    def get_file_history(self, file_path: str, count: int = 10) -> Dict[str, Any]:
        """Get commit history for a specific file"""
        result = self._run_git(
            "log", f"-{count}",
            "--format=%H|%an|%at|%s",
            "--", file_path
        )

        if not result['success']:
            return result

        commits = []
        for line in result['output'].strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 4:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'timestamp': int(parts[2]),
                    'message': parts[3]
                })

        return {
            'success': True,
            'file': file_path,
            'commits': commits
        }

    def show(self, commit: str, file: Optional[str] = None) -> Dict[str, Any]:
        """Show commit details or file at commit"""
        if file:
            return self._run_git("show", f"{commit}:{file}")
        return self._run_git("show", commit, "--stat")

    def blame(self, file_path: str) -> Dict[str, Any]:
        """Get blame information for a file"""
        result = self._run_git("blame", "--porcelain", file_path)

        if not result['success']:
            return result

        # Parse blame output (simplified)
        return {
            'success': True,
            'file': file_path,
            'raw': result['output']
        }
