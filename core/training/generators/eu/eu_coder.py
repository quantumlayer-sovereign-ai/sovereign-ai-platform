"""
EU Coder Generator - EU FinTech Code Generation Training Data

Generates training samples for eu_fintech_coder role focusing on:
- SEPA payment integration
- PSD2 SCA implementation
- GDPR-compliant code patterns
- Open Banking EU APIs
"""

import re
from ..base import BaseGenerator, TrainingSample


class EUCoderGenerator(BaseGenerator):
    """Generator for eu_fintech_coder role"""

    def __init__(self):
        super().__init__()
        self.role_name = "eu_fintech_coder"
        self.focus_areas = ["sepa_integration", "psd2_sca", "gdpr_code", "open_banking_eu"]
        self.compliance_tags = ["pci_dss", "gdpr", "psd2", "eidas"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate EU-specific code training samples"""
        samples = []

        # Extract code blocks for code generation samples
        samples.extend(self._generate_code_samples(content, source_file))

        # Generate SEPA-specific samples
        samples.extend(self._generate_sepa_samples(content, source_file))

        # Generate GDPR-specific samples
        samples.extend(self._generate_gdpr_samples(content, source_file))

        # Generate PSD2/SCA samples
        samples.extend(self._generate_psd2_samples(content, source_file))

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
                        instruction=f"Write a Python function called `{func_name}` for EU FinTech application",
                        input_text=docstring,
                        output=func_code.strip(),
                        category="function_implementation",
                        source_file=source_file
                    ))

        return samples

    def _generate_sepa_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate SEPA-specific samples"""
        samples = []

        sepa_keywords = ["sepa", "iban", "sct", "sdd", "iso20022", "pain.001"]
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code_lower = block["code"].lower()
            if any(kw in code_lower for kw in sepa_keywords):
                samples.append(self.create_sample(
                    instruction="Implement SEPA payment functionality in Python",
                    input_text="Follow ISO 20022 standards and validate IBAN format",
                    output=block["code"],
                    category="sepa_integration",
                    compliance_tags=["psd2"],
                    source_file=source_file
                ))

        return samples

    def _generate_gdpr_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate GDPR-specific samples"""
        samples = []

        gdpr_keywords = ["gdpr", "erasure", "portability", "consent", "personal_data", "dsr"]
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code_lower = block["code"].lower()
            if any(kw in code_lower for kw in gdpr_keywords):
                samples.append(self.create_sample(
                    instruction="Write GDPR-compliant data handling code in Python",
                    input_text="Ensure compliance with GDPR Articles 17, 20, and 32",
                    output=block["code"],
                    category="gdpr_code",
                    compliance_tags=["gdpr"],
                    source_file=source_file
                ))

        return samples

    def _generate_psd2_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate PSD2/SCA samples"""
        samples = []

        psd2_keywords = ["sca", "strong_customer_auth", "psd2", "tpp", "aisp", "pisp", "qwac"]
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code_lower = block["code"].lower()
            if any(kw in code_lower for kw in psd2_keywords):
                samples.append(self.create_sample(
                    instruction="Implement PSD2 Strong Customer Authentication in Python",
                    input_text="Use 2 of 3 factors: knowledge, possession, inherence",
                    output=block["code"],
                    category="psd2_sca",
                    compliance_tags=["psd2"],
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
        """Generate synthetic EU-specific samples"""
        samples = []

        # IBAN validation
        samples.append(self.create_sample(
            instruction="Write a Python function to validate IBAN format for SEPA payments",
            input_text="Validate country code, length, and MOD 97 checksum",
            output='''def validate_iban(iban: str) -> bool:
    """
    Validate IBAN format and checksum

    Args:
        iban: IBAN string to validate

    Returns:
        True if valid IBAN
    """
    # Remove spaces and convert to uppercase
    iban = iban.replace(" ", "").upper()

    # Check basic format
    if not re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]+$", iban):
        return False

    # Check length for country (simplified)
    if len(iban) < 15 or len(iban) > 34:
        return False

    # MOD 97 validation
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for char in rearranged:
        if char.isdigit():
            numeric += char
        else:
            numeric += str(ord(char) - 55)

    return int(numeric) % 97 == 1''',
            category="sepa_integration",
            compliance_tags=["psd2"]
        ))

        # SCA verification
        samples.append(self.create_sample(
            instruction="Implement PSD2 Strong Customer Authentication verification",
            input_text="Verify that 2 of 3 factors are present: knowledge, possession, inherence",
            output='''from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class AuthFactor(Enum):
    KNOWLEDGE = "knowledge"
    POSSESSION = "possession"
    INHERENCE = "inherence"

@dataclass
class SCAResult:
    verified: bool
    factors_used: list[AuthFactor]
    timestamp: datetime

def verify_sca(
    knowledge_verified: bool = False,
    possession_verified: bool = False,
    inherence_verified: bool = False
) -> SCAResult:
    """
    Verify Strong Customer Authentication per PSD2

    Args:
        knowledge_verified: Password/PIN verified
        possession_verified: Device/token verified
        inherence_verified: Biometric verified

    Returns:
        SCAResult with verification status
    """
    factors_used = []

    if knowledge_verified:
        factors_used.append(AuthFactor.KNOWLEDGE)
    if possession_verified:
        factors_used.append(AuthFactor.POSSESSION)
    if inherence_verified:
        factors_used.append(AuthFactor.INHERENCE)

    # PSD2 requires at least 2 factors from different categories
    verified = len(factors_used) >= 2

    return SCAResult(
        verified=verified,
        factors_used=factors_used,
        timestamp=datetime.utcnow()
    )''',
            category="psd2_sca",
            compliance_tags=["psd2"]
        ))

        # GDPR data erasure
        samples.append(self.create_sample(
            instruction="Implement GDPR Article 17 right to erasure handler",
            input_text="Delete user's personal data and notify processors",
            output='''async def handle_erasure_request(
    user_id: str,
    request_id: str
) -> dict:
    """
    Handle GDPR Article 17 erasure request

    Must delete personal data unless legal retention applies
    """
    import structlog
    from datetime import datetime

    logger = structlog.get_logger()

    # Check for legal holds
    legal_hold = await check_legal_retention(user_id)
    if legal_hold:
        logger.info(
            "erasure_partially_completed",
            user_id=user_id,
            reason="legal_retention"
        )
        return {
            "status": "partial",
            "reason": "Legal retention requirements apply"
        }

    # Delete from all systems
    await delete_personal_data(user_id)

    # Notify processors (Article 17(2))
    await notify_processors_of_deletion(user_id)

    # Audit log
    logger.info(
        "gdpr_erasure_completed",
        request_id=request_id,
        user_id=user_id,
        completed_at=datetime.utcnow().isoformat()
    )

    return {
        "status": "completed",
        "deleted_at": datetime.utcnow().isoformat()
    }''',
            category="gdpr_code",
            compliance_tags=["gdpr"]
        ))

        return samples
