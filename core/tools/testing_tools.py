"""
Testing Tools

Automated test execution and coverage analysis
"""

import subprocess
import json
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import structlog

logger = structlog.get_logger()


class TestRunner:
    """
    Test execution and coverage analysis

    Features:
    - Run pytest tests
    - Coverage reporting
    - Test result parsing
    - Failure analysis
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()

    def run_tests(
        self,
        test_path: Optional[str] = None,
        coverage: bool = True,
        verbose: bool = False,
        markers: Optional[List[str]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Run pytest tests

        Args:
            test_path: Specific test file/directory (default: tests/)
            coverage: Enable coverage reporting
            verbose: Verbose output
            markers: Pytest markers to filter tests
            timeout: Test timeout in seconds

        Returns:
            Dict with test results
        """
        test_path = test_path or "tests"
        full_test_path = self.project_path / test_path

        if not full_test_path.exists():
            return {
                'success': False,
                'error': f'Test path not found: {test_path}'
            }

        # Build pytest command
        cmd = ["python", "-m", "pytest", str(full_test_path)]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend([
                "--cov=" + str(self.project_path),
                "--cov-report=json",
                "--cov-report=term-missing"
            ])

        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        # Add JSON output for parsing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_report = f.name

        cmd.extend(["--json-report", f"--json-report-file={json_report}"])

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Parse results
            test_results = self._parse_results(json_report, result)

            # Parse coverage if enabled
            if coverage:
                coverage_data = self._parse_coverage()
                test_results['coverage'] = coverage_data

            return test_results

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Tests timed out after {timeout} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # Cleanup
            try:
                Path(json_report).unlink()
            except:
                pass

    def _parse_results(self, json_file: str, proc_result) -> Dict[str, Any]:
        """Parse pytest JSON report"""
        try:
            with open(json_file) as f:
                data = json.load(f)

            summary = data.get('summary', {})
            tests = data.get('tests', [])

            passed = [t for t in tests if t.get('outcome') == 'passed']
            failed = [t for t in tests if t.get('outcome') == 'failed']
            skipped = [t for t in tests if t.get('outcome') == 'skipped']
            errors = [t for t in tests if t.get('outcome') == 'error']

            return {
                'success': proc_result.returncode == 0,
                'return_code': proc_result.returncode,
                'summary': {
                    'total': len(tests),
                    'passed': len(passed),
                    'failed': len(failed),
                    'skipped': len(skipped),
                    'errors': len(errors),
                    'duration': summary.get('duration', 0)
                },
                'passed_tests': [t['nodeid'] for t in passed],
                'failed_tests': [
                    {
                        'name': t['nodeid'],
                        'message': t.get('call', {}).get('crash', {}).get('message', 'Unknown error'),
                        'traceback': t.get('call', {}).get('longrepr', '')[:500]
                    }
                    for t in failed
                ],
                'output': proc_result.stdout[:5000] if proc_result.stdout else ''
            }

        except (json.JSONDecodeError, FileNotFoundError):
            # Fallback to parsing stdout
            return self._parse_stdout(proc_result)

    def _parse_stdout(self, proc_result) -> Dict[str, Any]:
        """Parse pytest stdout when JSON not available"""
        output = proc_result.stdout or ''

        # Simple parsing
        passed = output.count(' passed')
        failed = output.count(' failed')
        errors = output.count(' error')

        return {
            'success': proc_result.returncode == 0,
            'return_code': proc_result.returncode,
            'summary': {
                'passed': passed,
                'failed': failed,
                'errors': errors
            },
            'output': output[:5000]
        }

    def _parse_coverage(self) -> Dict[str, Any]:
        """Parse coverage.json report"""
        coverage_file = self.project_path / "coverage.json"

        if not coverage_file.exists():
            return {'available': False}

        try:
            with open(coverage_file) as f:
                data = json.load(f)

            totals = data.get('totals', {})

            return {
                'available': True,
                'total_lines': totals.get('num_statements', 0),
                'covered_lines': totals.get('covered_lines', 0),
                'missing_lines': totals.get('missing_lines', 0),
                'coverage_percent': totals.get('percent_covered', 0),
                'files': {
                    name: {
                        'coverage': info.get('summary', {}).get('percent_covered', 0),
                        'missing': info.get('missing_lines', [])
                    }
                    for name, info in data.get('files', {}).items()
                }
            }

        except Exception as e:
            logger.warning("coverage_parse_failed", error=str(e))
            return {'available': False, 'error': str(e)}

    def run_single_test(self, test_name: str) -> Dict[str, Any]:
        """Run a single test by name"""
        cmd = [
            "python", "-m", "pytest",
            "-v",
            test_name
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                'success': result.returncode == 0,
                'test': test_name,
                'output': result.stdout[:2000],
                'error': result.stderr[:1000] if result.stderr else None
            }

        except Exception as e:
            return {
                'success': False,
                'test': test_name,
                'error': str(e)
            }

    def generate_test(self, code: str, function_name: str) -> str:
        """
        Generate test code for a function (template)

        This is a simplified template - actual test generation
        would use the AI model
        """
        return f'''
import pytest
from unittest.mock import Mock, patch

def test_{function_name}_success():
    """Test {function_name} with valid input"""
    # Arrange
    # TODO: Set up test data

    # Act
    # TODO: Call the function
    result = {function_name}()

    # Assert
    # TODO: Add assertions
    assert result is not None

def test_{function_name}_invalid_input():
    """Test {function_name} with invalid input"""
    # Arrange

    # Act & Assert
    with pytest.raises(ValueError):
        {function_name}(invalid_input)

def test_{function_name}_edge_case():
    """Test {function_name} edge cases"""
    # TODO: Add edge case tests
    pass
'''

    def list_tests(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """List all available tests"""
        test_path = test_path or "tests"

        cmd = [
            "python", "-m", "pytest",
            "--collect-only",
            "-q",
            str(self.project_path / test_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            tests = [
                line.strip()
                for line in result.stdout.split('\n')
                if line.strip() and '::' in line
            ]

            return {
                'success': True,
                'tests': tests,
                'count': len(tests)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class APITester:
    """
    API endpoint testing

    Features:
    - HTTP request execution
    - Response validation
    - Performance measurement
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def test_endpoint(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        expected_status: int = 200
    ) -> Dict[str, Any]:
        """Test an API endpoint"""
        import httpx
        from time import time

        url = f"{self.base_url}{path}"
        headers = headers or {}

        start_time = time()

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method.upper(),
                    url=url,
                    json=data,
                    headers=headers
                )

            duration = time() - start_time

            return {
                'success': response.status_code == expected_status,
                'url': url,
                'method': method.upper(),
                'status_code': response.status_code,
                'expected_status': expected_status,
                'duration_ms': round(duration * 1000, 2),
                'response_size': len(response.content),
                'body': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:500]
            }

        except Exception as e:
            return {
                'success': False,
                'url': url,
                'method': method.upper(),
                'error': str(e)
            }

    def run_test_suite(self, tests: List[Dict]) -> Dict[str, Any]:
        """Run a suite of API tests"""
        results = []

        for test in tests:
            result = self.test_endpoint(
                method=test.get('method', 'GET'),
                path=test['path'],
                data=test.get('data'),
                headers=test.get('headers'),
                expected_status=test.get('expected_status', 200)
            )
            result['test_name'] = test.get('name', test['path'])
            results.append(result)

        passed = sum(1 for r in results if r['success'])
        failed = len(results) - passed

        return {
            'success': failed == 0,
            'total': len(results),
            'passed': passed,
            'failed': failed,
            'results': results
        }
