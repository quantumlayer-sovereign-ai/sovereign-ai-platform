"""
Unit tests for compliance verification functionality
"""

from unittest.mock import MagicMock, patch

import pytest

from core.orchestrator.main import Orchestrator


class TestCodeExtraction:
    """Tests for code block extraction from agent results"""

    def test_extract_code_from_python_block(self):
        """Test extracting Python code block"""
        orchestrator = Orchestrator()
        results = [
            {
                "response": '''Here is the code:
```python
def hello():
    print("Hello, world!")
```
'''
            }
        ]

        code_blocks = orchestrator._extract_code_from_results(results)

        assert len(code_blocks) == 1
        assert "def hello():" in code_blocks[0][0]
        assert code_blocks[0][1] == "agent_0_block_0.py"

    def test_extract_code_from_py_block(self):
        """Test extracting py code block"""
        orchestrator = Orchestrator()
        results = [
            {
                "response": '''```py
x = 1
```'''
            }
        ]

        code_blocks = orchestrator._extract_code_from_results(results)

        assert len(code_blocks) == 1
        assert "x = 1" in code_blocks[0][0]

    def test_extract_code_from_unmarked_block(self):
        """Test extracting unmarked code block"""
        orchestrator = Orchestrator()
        results = [
            {
                "response": '''```
generic code
```'''
            }
        ]

        code_blocks = orchestrator._extract_code_from_results(results)

        assert len(code_blocks) == 1
        assert "generic code" in code_blocks[0][0]

    def test_extract_multiple_code_blocks(self):
        """Test extracting multiple code blocks from one response"""
        orchestrator = Orchestrator()
        results = [
            {
                "response": '''First block:
```python
block1 = True
```

Second block:
```python
block2 = True
```
'''
            }
        ]

        code_blocks = orchestrator._extract_code_from_results(results)

        assert len(code_blocks) == 2
        assert code_blocks[0][1] == "agent_0_block_0.py"
        assert code_blocks[1][1] == "agent_0_block_1.py"

    def test_extract_code_from_multiple_agents(self):
        """Test extracting code from multiple agent responses"""
        orchestrator = Orchestrator()
        results = [
            {"response": "```python\nagent1_code\n```"},
            {"response": "```python\nagent2_code\n```"},
        ]

        code_blocks = orchestrator._extract_code_from_results(results)

        assert len(code_blocks) == 2
        assert code_blocks[0][1] == "agent_0_block_0.py"
        assert code_blocks[1][1] == "agent_1_block_0.py"

    def test_extract_code_empty_response(self):
        """Test handling empty response"""
        orchestrator = Orchestrator()
        results = [{"response": ""}]

        code_blocks = orchestrator._extract_code_from_results(results)

        assert len(code_blocks) == 0

    def test_extract_code_no_code_blocks(self):
        """Test handling response without code blocks"""
        orchestrator = Orchestrator()
        results = [{"response": "This is just text without code."}]

        code_blocks = orchestrator._extract_code_from_results(results)

        assert len(code_blocks) == 0

    def test_extract_code_empty_code_block_skipped(self):
        """Test that empty code blocks are skipped"""
        orchestrator = Orchestrator()
        results = [
            {
                "response": '''```python
```

```python
valid_code = True
```'''
            }
        ]

        code_blocks = orchestrator._extract_code_from_results(results)

        # Should only have the non-empty block
        assert len(code_blocks) == 1
        assert "valid_code" in code_blocks[0][0]


class TestComplianceVerification:
    """Tests for the _verify_compliance method"""

    @pytest.mark.asyncio
    async def test_verify_compliance_no_code(self):
        """Test compliance passes when no code to check"""
        orchestrator = Orchestrator()
        results = [{"response": "No code here, just text."}]
        requirements = ["pci_dss", "rbi"]

        status = await orchestrator._verify_compliance(
            results, requirements, "fintech", "india"
        )

        # All requirements should pass when there's no code
        assert all(status.get(req, False) for req in requirements)
        assert status.get("_note")  # Note indicates no code checked

    @pytest.mark.asyncio
    async def test_verify_compliance_with_code_and_checker(self):
        """Test compliance verification with code and checker"""
        orchestrator = Orchestrator()
        results = [
            {"response": "```python\npassword = 'secret'\n```"}
        ]
        requirements = ["pci_dss"]

        with patch("core.orchestrator.main.SecurityScanner") as MockScanner:
            mock_scanner = MagicMock()
            mock_scanner.scan_code.return_value = {"passed": True, "issues": []}
            MockScanner.return_value = mock_scanner

            status = await orchestrator._verify_compliance(
                results, requirements, "fintech", "india"
            )

        assert "security_scan" in status

    @pytest.mark.asyncio
    async def test_verify_compliance_security_scan_fails(self):
        """Test compliance fails when security scan finds critical issues"""
        orchestrator = Orchestrator()
        results = [
            {"response": "```python\nimport os; os.system(user_input)\n```"}
        ]
        requirements = []

        with patch("core.orchestrator.main.SecurityScanner") as MockScanner:
            mock_scanner = MagicMock()
            mock_scanner.scan_code.return_value = {
                "passed": False,
                "issues": [{"severity": "critical", "rule_name": "command_injection"}]
            }
            MockScanner.return_value = mock_scanner

            status = await orchestrator._verify_compliance(
                results, requirements, "fintech", "india"
            )

        assert status.get("security_scan") is False

    @pytest.mark.asyncio
    async def test_verify_compliance_security_scanner_unavailable(self):
        """Test compliance handles scanner being unavailable"""
        orchestrator = Orchestrator()
        results = [{"response": "```python\ncode\n```"}]
        requirements = []

        with patch("core.orchestrator.main.SecurityScanner") as MockScanner:
            MockScanner.side_effect = Exception("Scanner unavailable")

            status = await orchestrator._verify_compliance(
                results, requirements, "fintech", "india"
            )

        # Should pass when scanner unavailable (graceful degradation)
        assert status.get("security_scan") is True

    @pytest.mark.asyncio
    async def test_verify_compliance_fintech_audit_logging(self):
        """Test fintech vertical always passes audit_logging"""
        orchestrator = Orchestrator()
        results = [{"response": "No code"}]
        requirements = ["audit_logging"]

        status = await orchestrator._verify_compliance(
            results, requirements, "fintech", "india"
        )

        assert status.get("audit_logging") is True

    @pytest.mark.asyncio
    async def test_verify_compliance_region_passed(self):
        """Test region parameter is accepted"""
        orchestrator = Orchestrator()
        results = [{"response": "No code"}]
        requirements = ["gdpr"]

        # Should not raise error
        status = await orchestrator._verify_compliance(
            results, requirements, "fintech", "eu"
        )

        assert "gdpr" in status


class TestComplianceWithChecker:
    """Tests for compliance verification with ComplianceChecker"""

    @pytest.mark.asyncio
    async def test_verify_compliance_checker_finds_issues(self):
        """Test compliance fails when checker finds critical issues"""
        orchestrator = Orchestrator()
        results = [{"response": "```python\ncode\n```"}]
        requirements = ["pci_dss"]

        mock_issue = MagicMock()
        mock_issue.rule_id = "pci_dss_001"
        mock_issue.rule_name = "PCI-DSS Violation"
        mock_issue.severity.value = "critical"

        mock_report = MagicMock()
        mock_report.issues = [mock_issue]

        with patch("verticals.fintech.compliance.ComplianceChecker") as MockChecker:
            mock_checker = MagicMock()
            mock_checker.check_code.return_value = mock_report
            MockChecker.return_value = mock_checker

            with patch("core.orchestrator.main.SecurityScanner") as MockScanner:
                mock_scanner = MagicMock()
                mock_scanner.scan_code.return_value = {"passed": True, "issues": []}
                MockScanner.return_value = mock_scanner

                status = await orchestrator._verify_compliance(
                    results, requirements, "fintech", "india"
                )

        assert status.get("pci_dss") is False

    @pytest.mark.asyncio
    async def test_verify_compliance_checker_no_issues(self):
        """Test compliance passes when checker finds no issues"""
        orchestrator = Orchestrator()
        results = [{"response": "```python\ncode\n```"}]
        requirements = ["pci_dss"]

        mock_report = MagicMock()
        mock_report.issues = []

        with patch("verticals.fintech.compliance.ComplianceChecker") as MockChecker:
            mock_checker = MagicMock()
            mock_checker.check_code.return_value = mock_report
            MockChecker.return_value = mock_checker

            with patch("core.orchestrator.main.SecurityScanner") as MockScanner:
                mock_scanner = MagicMock()
                mock_scanner.scan_code.return_value = {"passed": True, "issues": []}
                MockScanner.return_value = mock_scanner

                status = await orchestrator._verify_compliance(
                    results, requirements, "fintech", "india"
                )

        assert status.get("pci_dss") is True

    @pytest.mark.asyncio
    async def test_verify_compliance_low_severity_passes(self):
        """Test compliance passes when checker finds only low severity issues"""
        orchestrator = Orchestrator()
        results = [{"response": "```python\ncode\n```"}]
        requirements = ["pci_dss"]

        mock_issue = MagicMock()
        mock_issue.rule_id = "pci_dss_001"
        mock_issue.rule_name = "Minor Issue"
        mock_issue.severity.value = "low"

        mock_report = MagicMock()
        mock_report.issues = [mock_issue]

        with patch("verticals.fintech.compliance.ComplianceChecker") as MockChecker:
            mock_checker = MagicMock()
            mock_checker.check_code.return_value = mock_report
            MockChecker.return_value = mock_checker

            with patch("core.orchestrator.main.SecurityScanner") as MockScanner:
                mock_scanner = MagicMock()
                mock_scanner.scan_code.return_value = {"passed": True, "issues": []}
                MockScanner.return_value = mock_scanner

                status = await orchestrator._verify_compliance(
                    results, requirements, "fintech", "india"
                )

        # Low severity should still pass
        assert status.get("pci_dss") is True


class TestOrchestratorMemoryManagement:
    """Tests for orchestrator memory management"""

    def test_task_history_bounded(self):
        """Test that task history is bounded"""
        from core.orchestrator.main import MAX_HISTORY_SIZE, TaskResult

        orchestrator = Orchestrator()

        # Add more than MAX_HISTORY_SIZE tasks
        for i in range(MAX_HISTORY_SIZE + 50):
            result = TaskResult(
                task_id=f"task_{i}",
                success=True,
                results=[],
                aggregated_output="",
                compliance_status={},
                execution_time_seconds=0.1,
                agents_used=[],
                audit_trail=[]
            )
            orchestrator._append_task_history(result)

        assert len(orchestrator.task_history) <= MAX_HISTORY_SIZE

    def test_task_history_keeps_recent(self):
        """Test that task history keeps most recent entries"""
        from core.orchestrator.main import MAX_HISTORY_SIZE, TaskResult

        orchestrator = Orchestrator()

        # Add numbered tasks
        for i in range(MAX_HISTORY_SIZE + 10):
            result = TaskResult(
                task_id=f"task_{i}",
                success=True,
                results=[],
                aggregated_output="",
                compliance_status={},
                execution_time_seconds=0.1,
                agents_used=[],
                audit_trail=[]
            )
            orchestrator._append_task_history(result)

        # Last entry should have highest number
        assert orchestrator.task_history[-1].task_id == f"task_{MAX_HISTORY_SIZE + 9}"

        # First entry should NOT be task_0
        assert orchestrator.task_history[0].task_id != "task_0"
