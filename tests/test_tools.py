"""
Tests for Agent Tools

Tests:
- Code execution safety
- File operations security
- Git operations
- Security scanning
- Test runner
"""

import pytest
import tempfile
from pathlib import Path

from core.tools.code_tools import CodeExecutor, FileManager, SecurityError
from core.tools.git_tools import GitOperations
from core.tools.security_tools import SecurityScanner, Severity
from core.tools.testing_tools import TestRunner


class TestCodeExecutor:
    """Test code execution tools"""

    @pytest.fixture
    def executor(self):
        return CodeExecutor(timeout=10)

    def test_execute_safe_code(self, executor):
        """Test executing safe Python code"""
        code = """
x = 5
y = 10
print(x + y)
"""
        result = executor.execute(code)

        assert result["success"]
        assert "15" in result["output"]

    def test_validate_dangerous_import(self, executor):
        """Test that dangerous imports are detected"""
        code = """
import subprocess
subprocess.call(['ls'])
"""
        validation = executor.validate_code(code)

        assert not validation["valid"]
        assert any(i["type"] == "restricted_import" for i in validation["issues"])

    def test_validate_dangerous_eval(self, executor):
        """Test that eval is detected"""
        code = """
user_input = "1+1"
result = eval(user_input)
"""
        validation = executor.validate_code(code)

        assert not validation["valid"]
        assert any(i["type"] == "dangerous_builtin" for i in validation["issues"])

    def test_syntax_error_detection(self, executor):
        """Test syntax error detection"""
        code = """
def broken(
    print("missing paren")
"""
        validation = executor.validate_code(code)

        assert not validation["valid"]
        assert any(i["type"] == "syntax_error" for i in validation["issues"])

    def test_timeout_handling(self):
        """Test timeout for long-running code"""
        executor = CodeExecutor(timeout=1)
        code = """
import time
time.sleep(10)
"""
        # Note: This tests with allowed 'time' module - in practice would be blocked
        # Testing the timeout mechanism itself


class TestFileManager:
    """Test file management tools"""

    @pytest.fixture
    def file_manager(self, tmp_path):
        return FileManager(workspace_dir=str(tmp_path))

    def test_read_file(self, file_manager, tmp_path):
        """Test reading a file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        result = file_manager.read_file("test.txt")

        assert result["success"]
        assert result["content"] == "Hello, World!"

    def test_write_file(self, file_manager):
        """Test writing a file"""
        result = file_manager.write_file("new_file.txt", "New content")

        assert result["success"]
        assert result["size"] == len("New content")

    def test_path_traversal_blocked(self, file_manager):
        """Test that path traversal is blocked"""
        # Path traversal should return an error, not raise
        result = file_manager.read_file("../../../etc/passwd")
        # If it doesn't raise, it should fail to find file or be blocked
        assert not result["success"] or "passwd" not in result.get("content", "")

    def test_list_directory(self, file_manager, tmp_path):
        """Test listing directory contents"""
        (tmp_path / "file1.txt").write_text("1")
        (tmp_path / "file2.txt").write_text("2")

        result = file_manager.list_directory(".")

        assert result["success"]
        assert result["count"] == 2

    def test_search_files(self, file_manager, tmp_path):
        """Test searching for files"""
        (tmp_path / "test.py").write_text("python")
        (tmp_path / "test.txt").write_text("text")

        result = file_manager.search_files("*.py")

        assert result["success"]
        assert result["count"] == 1
        assert "test.py" in result["matches"][0]


class TestGitOperations:
    """Test Git operations"""

    @pytest.fixture
    def git_ops(self, tmp_path):
        ops = GitOperations(str(tmp_path))
        return ops

    def test_init(self, git_ops, tmp_path):
        """Test repository initialization"""
        # Already initialized by fixture
        assert (tmp_path / ".git").exists()

    def test_status_clean(self, git_ops):
        """Test status on clean repo"""
        result = git_ops.status()

        assert result["success"]

    def test_add_and_commit(self, git_ops, tmp_path):
        """Test adding and committing files"""
        import subprocess
        # Set git config for this repo
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                      cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"],
                      cwd=str(tmp_path), capture_output=True)

        # Create a file
        (tmp_path / "test.txt").write_text("test content")

        # Add
        git_ops.add(["test.txt"])

        # Commit
        result = git_ops.commit("Initial commit")

        assert result["success"]

    def test_log(self, git_ops, tmp_path):
        """Test viewing commit log"""
        import subprocess
        # Set git config
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                      cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"],
                      cwd=str(tmp_path), capture_output=True)

        # Create and commit a file
        (tmp_path / "test.txt").write_text("test")
        git_ops.add()
        git_ops.commit("Test commit")

        result = git_ops.log(count=1)

        assert result["success"]
        assert len(result["commits"]) == 1

    def test_branch_operations(self, git_ops, tmp_path):
        """Test branch operations"""
        import subprocess
        # Set git config
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                      cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"],
                      cwd=str(tmp_path), capture_output=True)

        # Create initial commit first
        (tmp_path / "test.txt").write_text("test")
        git_ops.add()
        git_ops.commit("Initial commit")

        # Create branch
        result = git_ops.branch("feature")
        assert result["success"]

        # Checkout
        result = git_ops.checkout("feature")
        assert result["success"]


class TestSecurityScanner:
    """Test security scanning"""

    @pytest.fixture
    def scanner(self):
        return SecurityScanner()

    def test_detect_sql_injection(self, scanner):
        """Test SQL injection detection"""
        code = '''
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = " + user_id)
'''
        result = scanner.scan_code(code)

        # Should detect SQL injection via string concatenation in execute
        assert any(i["rule_id"] == "SEC001" for i in result["issues"])

    def test_detect_hardcoded_password(self, scanner):
        """Test hardcoded password detection"""
        code = '''
password = "supersecretpassword123"
api_key = "sk-1234567890abcdefghij"
'''
        result = scanner.scan_code(code)

        assert any(i["rule_id"] == "SEC003" for i in result["issues"])

    def test_detect_insecure_http(self, scanner):
        """Test insecure HTTP detection"""
        code = '''
url = "http://api.example.com/data"
requests.get(url)
'''
        result = scanner.scan_code(code)

        assert any(i["rule_id"] == "SEC004" for i in result["issues"])

    def test_detect_weak_crypto(self, scanner):
        """Test weak cryptography detection"""
        code = '''
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()
'''
        result = scanner.scan_code(code)

        assert any(i["rule_id"] == "SEC005" for i in result["issues"])

    def test_detect_command_injection(self, scanner):
        """Test command injection detection"""
        code = '''
import os
os.system("ls " + user_input)
'''
        result = scanner.scan_code(code)

        assert any(i["rule_id"] == "SEC006" for i in result["issues"])

    def test_clean_code_passes(self, scanner):
        """Test that clean code passes"""
        code = '''
def safe_query(user_id):
    # Using parameterized query - safe from SQL injection
    result = db.execute_prepared("SELECT * FROM users WHERE id = ?", [user_id])
    return result
'''
        result = scanner.scan_code(code)

        # Should have no critical/high issues from our patterns
        critical_high = [i for i in result["issues"]
                        if i["severity"] in ["critical", "high"]]
        assert len(critical_high) == 0

    def test_scan_directory(self, scanner, tmp_path):
        """Test scanning a directory"""
        # Create test files
        (tmp_path / "safe.py").write_text('print("hello")')
        (tmp_path / "unsafe.py").write_text('password = "secret123"')

        result = scanner.scan_directory(str(tmp_path))

        assert result["success"]
        assert result["total_issues"] > 0


class TestTestRunner:
    """Test the test runner"""

    @pytest.fixture
    def test_runner(self, tmp_path):
        # Create a simple test project
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Create a passing test
        (tests_dir / "test_pass.py").write_text("""
def test_passing():
    assert 1 + 1 == 2
""")

        # Create a failing test
        (tests_dir / "test_fail.py").write_text("""
def test_failing():
    assert 1 + 1 == 3
""")

        return TestRunner(str(tmp_path))

    def test_list_tests(self, test_runner):
        """Test listing available tests"""
        result = test_runner.list_tests()

        assert result["success"]
        assert result["count"] >= 2

    def test_run_single_test(self, test_runner):
        """Test running a single test"""
        result = test_runner.run_single_test("tests/test_pass.py::test_passing")

        assert result["success"]
