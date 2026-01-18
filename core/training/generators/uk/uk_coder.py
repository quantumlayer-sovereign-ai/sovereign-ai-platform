"""
UK Coder Generator - UK FinTech Code Generation Training Data

Generates training samples for uk_fintech_coder role focusing on:
- Faster Payments integration
- Open Banking UK (OBIE)
- FCA-compliant code
- Confirmation of Payee implementation
"""

import re
from ..base import BaseGenerator, TrainingSample


class UKCoderGenerator(BaseGenerator):
    """Generator for uk_fintech_coder role"""

    def __init__(self):
        super().__init__()
        self.role_name = "uk_fintech_coder"
        self.focus_areas = ["fps_integration", "open_banking_uk", "fca_code", "cop_implementation"]
        self.compliance_tags = ["pci_dss", "uk_gdpr", "fca", "psr"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate UK-specific code training samples"""
        samples = []

        # Extract code blocks for code generation samples
        samples.extend(self._generate_code_samples(content, source_file))

        # Generate FPS-specific samples
        samples.extend(self._generate_fps_samples(content, source_file))

        # Generate CoP-specific samples
        samples.extend(self._generate_cop_samples(content, source_file))

        # Generate FCA-specific samples
        samples.extend(self._generate_fca_samples(content, source_file))

        return samples

    def _generate_code_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate samples from code blocks"""
        samples = []
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code = block["code"]

            # Extract function definitions
            func_matches = re.findall(
                r"((?:async\s+)?def\s+(\w+)\s*\([^)]*\)[^:]*:.*?)(?=\n(?:async\s+)?def\s|\nclass\s|\Z)",
                code,
                re.DOTALL
            )

            for func_code, func_name in func_matches:
                if func_name.startswith("_") and not func_name.startswith("__"):
                    continue

                docstring = self._extract_function_docstring(func_code)
                if docstring:
                    samples.append(self.create_sample(
                        instruction=f"Write a Python function called `{func_name}` for UK FinTech application",
                        input_text=docstring,
                        output=func_code.strip(),
                        category="function_implementation",
                        source_file=source_file
                    ))

        return samples

    def _generate_fps_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate Faster Payments specific samples"""
        samples = []

        fps_keywords = ["faster_payment", "fps", "sort_code", "bacs", "chaps"]
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code_lower = block["code"].lower()
            if any(kw in code_lower for kw in fps_keywords):
                samples.append(self.create_sample(
                    instruction="Implement UK payment scheme integration in Python",
                    input_text="Support Faster Payments, BACS, and CHAPS",
                    output=block["code"],
                    category="fps_integration",
                    compliance_tags=["psr"],
                    source_file=source_file
                ))

        return samples

    def _generate_cop_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate Confirmation of Payee samples"""
        samples = []

        cop_keywords = ["confirm_payee", "cop", "payee_name", "name_match"]
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code_lower = block["code"].lower()
            if any(kw in code_lower for kw in cop_keywords):
                samples.append(self.create_sample(
                    instruction="Implement Confirmation of Payee check in Python",
                    input_text="Check payee name before payment as required by PSR",
                    output=block["code"],
                    category="cop_implementation",
                    compliance_tags=["psr"],
                    source_file=source_file
                ))

        return samples

    def _generate_fca_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate FCA-specific samples"""
        samples = []

        fca_keywords = ["consumer_duty", "customer_outcome", "fair_value", "fca"]
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code_lower = block["code"].lower()
            if any(kw in code_lower for kw in fca_keywords):
                samples.append(self.create_sample(
                    instruction="Implement FCA-compliant functionality in Python",
                    input_text="Ensure Consumer Duty compliance",
                    output=block["code"],
                    category="fca_code",
                    compliance_tags=["fca"],
                    source_file=source_file
                ))

        return samples

    def _extract_function_docstring(self, func_code: str) -> str:
        """Extract docstring from function"""
        lines = func_code.split("\n")
        in_docstring = False
        docstring_lines = []

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    break
                else:
                    in_docstring = True
                    if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        return stripped.strip("\"'")
            elif in_docstring:
                docstring_lines.append(stripped)

        return " ".join(docstring_lines).strip()

    def generate_synthetic_samples(self) -> list[TrainingSample]:
        """Generate synthetic UK-specific samples"""
        samples = []

        # Sort code validation
        samples.append(self.create_sample(
            instruction="Write a Python function to validate UK sort code and account number",
            input_text="Validate format and perform modulus check",
            output='''def validate_uk_account(sort_code: str, account_number: str) -> bool:
    """
    Validate UK sort code and account number

    Args:
        sort_code: 6-digit sort code (with or without hyphens)
        account_number: 8-digit account number

    Returns:
        True if valid format
    """
    import re

    # Clean sort code
    sort_code = sort_code.replace("-", "").replace(" ", "")

    # Validate format
    if not re.match(r"^\\d{6}$", sort_code):
        return False

    if not re.match(r"^\\d{8}$", account_number):
        return False

    # Additional modulus check would be performed here
    # using the modulus weight table

    return True


def format_sort_code(sort_code: str) -> str:
    """Format sort code with hyphens"""
    clean = sort_code.replace("-", "").replace(" ", "")
    if len(clean) == 6:
        return f"{clean[:2]}-{clean[2:4]}-{clean[4:6]}"
    return sort_code''',
            category="fps_integration",
            compliance_tags=["psr"]
        ))

        # Confirmation of Payee
        samples.append(self.create_sample(
            instruction="Implement Confirmation of Payee check for UK payments",
            input_text="Check payee name matches account holder per PSR requirements",
            output='''from enum import Enum
from dataclasses import dataclass
from typing import Optional

class CoPResult(Enum):
    MATCH = "match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    NOT_AVAILABLE = "not_available"

@dataclass
class CoPCheck:
    result: CoPResult
    account_name_provided: str
    actual_name: Optional[str] = None
    match_score: float = 0.0

async def confirm_payee(
    name: str,
    sort_code: str,
    account_number: str
) -> CoPCheck:
    """
    Perform Confirmation of Payee check

    Args:
        name: Payee name entered by user
        sort_code: Recipient sort code
        account_number: Recipient account number

    Returns:
        CoPCheck with match result
    """
    # Query receiving bank
    response = await query_cop_service(
        sort_code=sort_code,
        account_number=account_number,
        name=name
    )

    if response.get("status") == "not_available":
        return CoPCheck(
            result=CoPResult.NOT_AVAILABLE,
            account_name_provided=name
        )

    # Calculate match score
    actual_name = response.get("account_name", "")
    match_score = calculate_name_similarity(name, actual_name)

    if match_score >= 0.95:
        result = CoPResult.MATCH
    elif match_score >= 0.70:
        result = CoPResult.PARTIAL_MATCH
    else:
        result = CoPResult.NO_MATCH

    return CoPCheck(
        result=result,
        account_name_provided=name,
        actual_name=actual_name if result != CoPResult.MATCH else None,
        match_score=match_score
    )


def show_cop_warning(cop_check: CoPCheck) -> dict:
    """Generate user-facing warning for CoP result"""
    if cop_check.result == CoPResult.NO_MATCH:
        return {
            "title": "Warning: Name does not match",
            "message": f"The name you entered ({cop_check.account_name_provided}) "
                      f"does not match the account holder ({cop_check.actual_name}). "
                      "This could be a sign of fraud.",
            "severity": "critical"
        }
    elif cop_check.result == CoPResult.PARTIAL_MATCH:
        return {
            "title": "The name doesn\'t quite match",
            "message": f"Did you mean: {cop_check.actual_name}?",
            "severity": "warning"
        }
    return {"title": None, "message": None, "severity": None}''',
            category="cop_implementation",
            compliance_tags=["psr"]
        ))

        # Consumer Duty outcome monitoring
        samples.append(self.create_sample(
            instruction="Implement Consumer Duty outcome monitoring for FCA compliance",
            input_text="Track and assess customer outcomes",
            output='''from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import structlog

logger = structlog.get_logger()

class OutcomeType(Enum):
    PRODUCTS_SERVICES = "products_and_services"
    PRICE_VALUE = "price_and_value"
    CONSUMER_UNDERSTANDING = "consumer_understanding"
    CONSUMER_SUPPORT = "consumer_support"

@dataclass
class CustomerOutcome:
    customer_id: str
    outcome_type: OutcomeType
    score: float  # 0-1
    issues: list[str]
    assessed_at: datetime

def assess_customer_outcome(
    customer_id: str,
    product_id: str,
    interaction_data: dict
) -> CustomerOutcome:
    """
    Assess customer outcome for Consumer Duty compliance

    PRIN 2A requires acting to deliver good outcomes
    """
    # Determine outcome type from interaction
    outcome_type = determine_outcome_type(interaction_data)

    # Collect outcome metrics
    metrics = collect_outcome_metrics(customer_id, product_id)

    # Score the outcome
    score = calculate_outcome_score(metrics)

    # Identify any issues
    issues = identify_outcome_issues(metrics, score)

    outcome = CustomerOutcome(
        customer_id=customer_id,
        outcome_type=outcome_type,
        score=score,
        issues=issues,
        assessed_at=datetime.utcnow()
    )

    # Log for monitoring
    logger.info(
        "customer_outcome_assessed",
        customer_id=customer_id,
        outcome_type=outcome_type.value,
        score=score,
        issues_count=len(issues)
    )

    # Alert if poor outcome
    if score < 0.5:
        logger.warning(
            "poor_customer_outcome",
            customer_id=customer_id,
            score=score,
            issues=issues
        )

    return outcome


def monitor_outcomes(product_id: str, period_days: int = 30) -> dict:
    """
    Monitor customer outcomes at product level

    FCA Consumer Duty requires ongoing monitoring
    """
    outcomes = get_product_outcomes(product_id, period_days)

    if not outcomes:
        return {"status": "no_data"}

    avg_score = sum(o.score for o in outcomes) / len(outcomes)
    failure_rate = len([o for o in outcomes if o.score < 0.5]) / len(outcomes)

    return {
        "product_id": product_id,
        "period_days": period_days,
        "total_outcomes": len(outcomes),
        "average_score": avg_score,
        "failure_rate": failure_rate,
        "requires_action": failure_rate > 0.1 or avg_score < 0.7
    }''',
            category="fca_code",
            compliance_tags=["fca"]
        ))

        return samples
