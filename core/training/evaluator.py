"""
Evaluator for LoRA Adapter Performance

Provides compliance benchmarks and quality metrics for trained adapters.

Benchmarks:
1. Compliance accuracy (detect PCI-DSS violations)
2. Code quality (syntax, security patterns)
3. Knowledge recall (regulatory citations)
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class EvaluationResult:
    """Results from adapter evaluation"""
    role: str
    adapter_version: str
    timestamp: datetime
    overall_score: float
    metrics: dict[str, float]
    detailed_results: list[dict]
    passed: bool

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "adapter_version": self.adapter_version,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": self.overall_score,
            "metrics": self.metrics,
            "detailed_results": self.detailed_results,
            "passed": self.passed
        }


@dataclass
class TestCase:
    """Single evaluation test case"""
    id: str
    category: str
    prompt: str
    expected_patterns: list[str]  # Regex patterns to find
    forbidden_patterns: list[str] = field(default_factory=list)  # Must NOT appear
    compliance_tags: list[str] = field(default_factory=list)
    weight: float = 1.0


class AdapterEvaluator:
    """
    Evaluator for trained LoRA adapters

    Tests adapters against role-specific benchmarks including:
    - Compliance accuracy
    - Code quality
    - Security pattern detection
    - Knowledge recall
    """

    def __init__(self, model_interface=None):
        self.model = model_interface
        self.test_cases: dict[str, list[TestCase]] = self._load_test_cases()

    def _load_test_cases(self) -> dict[str, list[TestCase]]:
        """Load test cases for each role"""
        return {
            "fintech_coder": self._coder_test_cases(),
            "fintech_security": self._security_test_cases(),
            "fintech_compliance": self._compliance_test_cases(),
            "fintech_architect": self._architect_test_cases(),
            "fintech_tester": self._tester_test_cases(),
        }

    def _coder_test_cases(self) -> list[TestCase]:
        """Test cases for fintech_coder"""
        return [
            TestCase(
                id="coder_001",
                category="secure_coding",
                prompt="Write a function to mask a credit card number for display",
                expected_patterns=[
                    r"def\s+\w*mask\w*\s*\(",  # Function definition
                    r"\[:6\]|\[-4:\]|first\s*6|last\s*4",  # Masking logic
                ],
                forbidden_patterns=[
                    r"print\s*\(\s*card",  # Don't print raw card
                ],
                compliance_tags=["PCI-3.3"],
                weight=2.0
            ),
            TestCase(
                id="coder_002",
                category="sql_security",
                prompt="Write a function to query a user by ID from the database",
                expected_patterns=[
                    r"%s|%\(|\?|:\w+",  # Parameterized query
                    r"execute\s*\(\s*['\"][^+%f]+['\"]",  # Proper execute call
                ],
                forbidden_patterns=[
                    r"f['\"].*{.*}",  # f-string interpolation
                    r"\+\s*str\s*\(|str\s*\(.*\)\s*\+",  # String concatenation
                ],
                compliance_tags=["PCI-6.5.1"],
                weight=2.0
            ),
            TestCase(
                id="coder_003",
                category="money_handling",
                prompt="Write a function to calculate total payment including tax",
                expected_patterns=[
                    r"Decimal|decimal",  # Use Decimal
                ],
                forbidden_patterns=[
                    r"float\s*\(|\.0\s*\*|/\s*100\.0",  # Float arithmetic
                ],
                compliance_tags=["PCI-6"],
                weight=1.5
            ),
            TestCase(
                id="coder_004",
                category="api_security",
                prompt="Write code to call a payment gateway API",
                expected_patterns=[
                    r"os\.environ|getenv|config\.",  # Environment variables
                    r"https://",  # HTTPS
                ],
                forbidden_patterns=[
                    r"api_key\s*=\s*['\"][a-zA-Z0-9]+['\"]",  # Hardcoded keys
                    r"http://(?!localhost)",  # HTTP (except localhost)
                ],
                compliance_tags=["PCI-4.1"],
                weight=2.0
            ),
            TestCase(
                id="coder_005",
                category="logging",
                prompt="Write a payment logging function that logs transaction details",
                expected_patterns=[
                    r"mask|redact|\*+",  # Masking logic
                    r"transaction_id|txn_id",  # Transaction reference
                ],
                forbidden_patterns=[
                    r"card.*number|pan\s*=|cvv|pin",  # Sensitive data in logs
                ],
                compliance_tags=["PCI-10.3"],
                weight=2.0
            ),
        ]

    def _security_test_cases(self) -> list[TestCase]:
        """Test cases for fintech_security"""
        return [
            TestCase(
                id="security_001",
                category="vuln_detection",
                prompt="Review this code for security issues:\ndef get_user(id): return db.execute(f'SELECT * FROM users WHERE id={id}')",
                expected_patterns=[
                    r"sql\s*injection|injection",
                    r"parameterized|prepared|sanitize",
                    r"critical|high|severe",
                ],
                compliance_tags=["PCI-6.5.1"],
                weight=2.0
            ),
            TestCase(
                id="security_002",
                category="pci_compliance",
                prompt="What are the key PCI-DSS requirements for storing cardholder data?",
                expected_patterns=[
                    r"requirement\s*3|encrypt|mask",
                    r"AES|256|aes-256",
                    r"never.*store.*cvv|cvv.*never.*stored",
                ],
                compliance_tags=["PCI-3"],
                weight=1.5
            ),
            TestCase(
                id="security_003",
                category="encryption",
                prompt="What encryption standards should be used for card data at rest?",
                expected_patterns=[
                    r"AES-256|aes.256",
                    r"key\s*management|HSM",
                ],
                forbidden_patterns=[
                    r"MD5|DES|SHA1(?!-)",  # Weak algorithms
                ],
                compliance_tags=["PCI-3.4"],
                weight=2.0
            ),
            TestCase(
                id="security_004",
                category="access_control",
                prompt="How should access to cardholder data be controlled?",
                expected_patterns=[
                    r"need.to.know|least\s*privilege|RBAC",
                    r"multi.factor|MFA|2FA",
                    r"audit|log",
                ],
                compliance_tags=["PCI-7", "PCI-8"],
                weight=1.5
            ),
        ]

    def _compliance_test_cases(self) -> list[TestCase]:
        """Test cases for fintech_compliance"""
        return [
            TestCase(
                id="compliance_001",
                category="rbi_guidelines",
                prompt="What are the RBI data localization requirements for payment data?",
                expected_patterns=[
                    r"india|domestic",
                    r"stored|storage|locali[sz]",
                    r"24\s*hours?|end.of.day",
                ],
                compliance_tags=["RBI-DL"],
                weight=2.0
            ),
            TestCase(
                id="compliance_002",
                category="dpdp_act",
                prompt="What are the consent requirements under the DPDP Act?",
                expected_patterns=[
                    r"consent|permission",
                    r"purpose|specific",
                    r"withdraw|revoke",
                ],
                compliance_tags=["DPDP"],
                weight=1.5
            ),
            TestCase(
                id="compliance_003",
                category="payment_aggregator",
                prompt="What are the net worth requirements for payment aggregators as per RBI?",
                expected_patterns=[
                    r"15\s*crore|25\s*crore|crore",
                    r"net\s*worth|capital",
                ],
                compliance_tags=["RBI-PA"],
                weight=1.5
            ),
            TestCase(
                id="compliance_004",
                category="breach_notification",
                prompt="What is the timeline for data breach notification under DPDP?",
                expected_patterns=[
                    r"72\s*hours?|3\s*days?",
                    r"notify|inform|report",
                    r"board|authority|DPA",
                ],
                compliance_tags=["DPDP"],
                weight=1.5
            ),
        ]

    def _architect_test_cases(self) -> list[TestCase]:
        """Test cases for fintech_architect"""
        return [
            TestCase(
                id="architect_001",
                category="payment_design",
                prompt="Design a high-availability payment gateway architecture",
                expected_patterns=[
                    r"load\s*balanc|redundan|failover",
                    r"multi.az|region|zone",
                    r"99\.9|availability",
                ],
                compliance_tags=["PCI-DSS"],
                weight=1.5
            ),
            TestCase(
                id="architect_002",
                category="security_arch",
                prompt="What security controls should be in place for a payment processing system?",
                expected_patterns=[
                    r"encrypt|TLS|firewall|WAF",
                    r"token|HSM|vault",
                    r"audit|monitor|SIEM",
                ],
                compliance_tags=["PCI-DSS"],
                weight=2.0
            ),
            TestCase(
                id="architect_003",
                category="patterns",
                prompt="How would you handle distributed transactions in a payment system?",
                expected_patterns=[
                    r"saga|event.sourc|CQRS|idempoten",
                    r"compensat|rollback|eventual",
                ],
                compliance_tags=["PCI-DSS"],
                weight=1.5
            ),
        ]

    def _tester_test_cases(self) -> list[TestCase]:
        """Test cases for fintech_tester"""
        return [
            TestCase(
                id="tester_001",
                category="test_generation",
                prompt="Write test cases for a payment refund API",
                expected_patterns=[
                    r"def\s+test_|@pytest|assert",
                    r"refund|success|fail",
                    r"partial|full|amount",
                ],
                compliance_tags=["PCI-DSS"],
                weight=1.5
            ),
            TestCase(
                id="tester_002",
                category="security_testing",
                prompt="What security tests should be performed on a payment API?",
                expected_patterns=[
                    r"sql.*injection|xss|auth",
                    r"rate.*limit|brute.*force",
                    r"penetration|OWASP",
                ],
                compliance_tags=["PCI-11"],
                weight=2.0
            ),
            TestCase(
                id="tester_003",
                category="test_data",
                prompt="What test card numbers should be used for payment testing?",
                expected_patterns=[
                    r"4111|test.*card|sandbox",
                ],
                forbidden_patterns=[
                    r"real.*card|production",
                ],
                compliance_tags=["PCI-DSS"],
                weight=1.0
            ),
        ]

    async def evaluate_adapter(
        self,
        role: str,
        adapter_path: Path | None = None
    ) -> EvaluationResult:
        """
        Evaluate an adapter against role-specific test cases

        Args:
            role: Role to evaluate
            adapter_path: Path to adapter (uses active if None)

        Returns:
            EvaluationResult with scores and details
        """
        if role not in self.test_cases:
            raise ValueError(f"No test cases for role: {role}")

        test_cases = self.test_cases[role]
        results = []
        total_score = 0
        max_score = 0

        for test in test_cases:
            result = await self._run_test_case(test)
            results.append(result)
            total_score += result["score"] * test.weight
            max_score += test.weight

        overall_score = total_score / max_score if max_score > 0 else 0
        passed = overall_score >= 0.7  # 70% threshold

        # Calculate category metrics
        category_scores = {}
        for result in results:
            cat = result["category"]
            if cat not in category_scores:
                category_scores[cat] = {"total": 0, "count": 0}
            category_scores[cat]["total"] += result["score"]
            category_scores[cat]["count"] += 1

        metrics = {
            cat: scores["total"] / scores["count"]
            for cat, scores in category_scores.items()
        }
        metrics["overall"] = overall_score

        return EvaluationResult(
            role=role,
            adapter_version=str(adapter_path) if adapter_path else "base",
            timestamp=datetime.now(),
            overall_score=overall_score,
            metrics=metrics,
            detailed_results=results,
            passed=passed
        )

    async def _run_test_case(self, test: TestCase) -> dict:
        """Run a single test case"""
        # Generate response
        if self.model:
            messages = [{"role": "user", "content": test.prompt}]
            response = await self.model.generate(messages)
        else:
            # Mock response for testing without model
            response = "Mock response for testing"

        # Evaluate response
        expected_matches = sum(
            1 for pattern in test.expected_patterns
            if re.search(pattern, response, re.IGNORECASE)
        )

        forbidden_matches = sum(
            1 for pattern in test.forbidden_patterns
            if re.search(pattern, response, re.IGNORECASE)
        )

        # Calculate score
        expected_score = expected_matches / len(test.expected_patterns) if test.expected_patterns else 1.0
        forbidden_penalty = min(forbidden_matches * 0.3, 0.6)  # Up to 60% penalty
        score = max(0, expected_score - forbidden_penalty)

        return {
            "test_id": test.id,
            "category": test.category,
            "prompt": test.prompt[:100] + "...",
            "expected_matches": expected_matches,
            "expected_total": len(test.expected_patterns),
            "forbidden_matches": forbidden_matches,
            "score": score,
            "passed": score >= 0.6,
            "compliance_tags": test.compliance_tags
        }

    def save_results(
        self,
        result: EvaluationResult,
        output_path: Path
    ):
        """Save evaluation results to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info("evaluation_saved", path=str(output_path), score=result.overall_score)

    def compare_adapters(
        self,
        result1: EvaluationResult,
        result2: EvaluationResult
    ) -> dict:
        """Compare two evaluation results"""
        return {
            "adapter1": {
                "version": result1.adapter_version,
                "score": result1.overall_score,
            },
            "adapter2": {
                "version": result2.adapter_version,
                "score": result2.overall_score,
            },
            "improvement": result2.overall_score - result1.overall_score,
            "category_comparison": {
                cat: result2.metrics.get(cat, 0) - result1.metrics.get(cat, 0)
                for cat in set(result1.metrics.keys()) | set(result2.metrics.keys())
            }
        }


class ComplianceAuditor:
    """
    Specialized auditor for compliance testing

    Runs compliance-specific checks against generated code/responses
    """

    PCI_PATTERNS = {
        "PCI-3.3": {
            "description": "Mask PAN when displayed",
            "required": [r"\*+|mask|first.*6.*last.*4"],
            "forbidden": [r"full.*pan|display.*card.*number"],
        },
        "PCI-3.4": {
            "description": "Render PAN unreadable",
            "required": [r"encrypt|hash|token"],
            "forbidden": [r"plain.*text|unencrypt"],
        },
        "PCI-4.1": {
            "description": "Use strong cryptography",
            "required": [r"TLS|HTTPS|SSL"],
            "forbidden": [r"HTTP(?!S)|telnet|FTP(?!S)"],
        },
        "PCI-6.5.1": {
            "description": "Prevent injection flaws",
            "required": [r"parameterized|prepared|sanitize|escape"],
            "forbidden": [r"f['\"].*\{|string.*concat|format.*%"],
        },
    }

    def audit_response(self, response: str, required_tags: list[str]) -> dict:
        """Audit a response for compliance"""
        results = {}

        for tag in required_tags:
            if tag not in self.PCI_PATTERNS:
                continue

            pattern_def = self.PCI_PATTERNS[tag]
            required_found = any(
                re.search(p, response, re.IGNORECASE)
                for p in pattern_def["required"]
            )
            forbidden_found = any(
                re.search(p, response, re.IGNORECASE)
                for p in pattern_def["forbidden"]
            )

            results[tag] = {
                "description": pattern_def["description"],
                "required_patterns_found": required_found,
                "forbidden_patterns_found": forbidden_found,
                "compliant": required_found and not forbidden_found
            }

        return results
