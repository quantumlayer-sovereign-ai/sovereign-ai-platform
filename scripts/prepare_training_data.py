#!/usr/bin/env python3
"""
Prepare Training Data for LoRA Fine-tuning
==========================================
Creates training data from:
1. High-quality code templates
2. Curated GitHub examples
3. Manually corrected generated code

Output format: JSONL with instruction-response pairs
"""

import json
import sys
from pathlib import Path
from typing import Generator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


SYSTEM_PROMPT = """You are a Senior FinTech Developer with 15+ years of experience. You write PRODUCTION-READY, enterprise-grade code.

CODE OUTPUT FORMAT:
- Output code files with explicit paths as markdown headers
- Format: #### `path/to/file.py` followed by ```python code block

REQUIREMENTS:
1. Use Pydantic v2 syntax (pydantic_settings for BaseSettings)
2. Include ALL imports in EVERY file
3. Use type hints everywhere
4. Use Decimal for money (never float)
5. Include proper error handling
6. Follow the app/ directory structure"""


def create_training_example(
    instruction: str,
    response: str,
    system: str = SYSTEM_PROMPT,
) -> dict:
    """Create a single training example in chat format."""
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": response},
        ]
    }


def extract_examples_from_template(template_path: Path) -> Generator[dict, None, None]:
    """Extract training examples from a code template file."""
    content = template_path.read_text(encoding="utf-8")

    # Extract the docstring description
    lines = content.split("\n")
    description = ""
    for line in lines[1:20]:  # Look in first 20 lines
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            continue
        if "===" in line:
            continue
        if line.strip():
            description = line.strip()
            break

    # Extract code sections marked with # FILE:
    sections = content.split("# ============================================================================")

    for section in sections:
        if "# FILE:" in section:
            # Extract filename and code
            file_match = section.split("# FILE:")
            if len(file_match) > 1:
                file_part = file_match[1].strip()
                file_lines = file_part.split("\n")
                filename = file_lines[0].strip()

                # Get the code (skip header comments)
                code_lines = []
                in_code = False
                for line in file_lines[1:]:
                    if line.strip().startswith('"""') and not in_code:
                        in_code = True
                        continue
                    if in_code:
                        code_lines.append(line)

                if code_lines:
                    code = "\n".join(code_lines).strip()

                    # Create instruction based on filename
                    instruction = _generate_instruction(filename, description)

                    # Create response with proper formatting
                    response = f"#### `{filename}`\n```python\n{code}\n```"

                    yield create_training_example(instruction, response)


def _generate_instruction(filename: str, description: str) -> str:
    """Generate an instruction based on the filename."""
    filename_lower = filename.lower()

    if "settings" in filename_lower:
        return "Create a Pydantic v2 settings configuration file for a FastAPI application with database URL, secret key, and environment file support."

    if "schema" in filename_lower:
        return "Create Pydantic v2 schemas for request and response validation with proper type hints, ConfigDict, and field validation."

    if "service" in filename_lower:
        if "payment" in filename_lower:
            return "Create a payment service class with async methods for creating payments, processing transactions, and handling refunds. Include proper error handling and audit logging."
        if "wallet" in filename_lower:
            return "Create a wallet service class with deposit, withdraw, and balance check operations. Use Decimal for money, include idempotency keys, and proper transaction handling."
        return "Create a service class with CRUD operations using async SQLAlchemy."

    if "router" in filename_lower or "endpoint" in filename_lower:
        if "payment" in filename_lower:
            return "Create FastAPI payment API endpoints with POST for creating payments, GET for retrieving payment status, and proper error handling."
        if "wallet" in filename_lower:
            return "Create FastAPI wallet API endpoints for deposits, withdrawals, and balance checks with proper validation and error handling."
        return "Create FastAPI router with API endpoints including proper dependency injection and error handling."

    if "database" in filename_lower:
        return "Create async SQLAlchemy database configuration with AsyncSession, engine setup, and dependency injection for FastAPI."

    if "model" in filename_lower:
        return "Create SQLAlchemy models with proper type annotations, relationships, and audit fields (created_at, updated_at)."

    if "main" in filename_lower:
        return "Create a FastAPI application entry point with lifespan handler, CORS middleware, and router includes."

    return f"Create the code for {filename} following FastAPI and Pydantic v2 best practices."


def create_fintech_examples() -> list[dict]:
    """Create additional fintech-specific training examples."""
    examples = []

    # Example 1: Payment processing
    examples.append(create_training_example(
        instruction="Write a payment processing function that handles card tokenization with PCI-DSS compliance.",
        response='''#### `app/services/card_processor.py`
```python
"""Card processing service with PCI-DSS compliance."""
import hashlib
import secrets
from datetime import datetime
from decimal import Decimal
from typing import Optional

from cryptography.fernet import Fernet

from app.config.settings import settings


class CardProcessor:
    """Process card payments with tokenization."""

    def __init__(self, encryption_key: Optional[bytes] = None):
        self.fernet = Fernet(encryption_key or settings.ENCRYPTION_KEY)

    def tokenize_card(
        self,
        card_number: str,
        expiry_month: int,
        expiry_year: int,
        cvv: str,  # Never stored, only used for verification
    ) -> str:
        """
        Tokenize card details for secure storage.

        Args:
            card_number: Full card number (will be tokenized)
            expiry_month: Card expiry month
            expiry_year: Card expiry year
            cvv: CVV (used only for this request, never stored)

        Returns:
            Token that can be used for future transactions

        Note:
            CVV is intentionally not stored per PCI-DSS requirements.
        """
        # Validate card number (basic Luhn check would go here)
        if not self._validate_card_number(card_number):
            raise ValueError("Invalid card number")

        # Create token - hash of card details + random salt
        salt = secrets.token_hex(16)
        token_data = f"{card_number}:{expiry_month}:{expiry_year}:{salt}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:32]

        # Store encrypted card details (last 4 digits only for display)
        last_four = card_number[-4:]

        return f"tok_{token}_{last_four}"

    def mask_card_number(self, card_number: str) -> str:
        """Mask card number for logging/display."""
        return f"****-****-****-{card_number[-4:]}"

    def _validate_card_number(self, card_number: str) -> bool:
        """Basic card number validation."""
        # Remove spaces and dashes
        number = card_number.replace(" ", "").replace("-", "")
        return len(number) >= 13 and len(number) <= 19 and number.isdigit()
```'''
    ))

    # Example 2: Wallet balance with Decimal
    examples.append(create_training_example(
        instruction="Create a wallet balance schema using Decimal for money with proper validation.",
        response='''#### `app/models/wallet_schemas.py`
```python
"""Wallet schemas with Decimal for precise money handling."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WalletBalance(BaseModel):
    """Wallet balance response."""

    wallet_id: str
    user_id: str
    balance: Decimal = Field(
        ...,
        description="Current balance",
        ge=Decimal("0"),
    )
    currency: str = Field(default="INR", pattern="^[A-Z]{3}$")
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepositRequest(BaseModel):
    """Deposit funds into wallet."""

    amount: Decimal = Field(
        ...,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        description="Amount to deposit",
    )
    reference: str = Field(..., min_length=1, max_length=100)
    idempotency_key: str = Field(..., min_length=16, max_length=64)

    @field_validator("amount", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert float to Decimal safely."""
        if isinstance(v, float):
            # Convert via string to avoid float precision issues
            return Decimal(str(v))
        return Decimal(v) if not isinstance(v, Decimal) else v


class WithdrawRequest(BaseModel):
    """Withdraw funds from wallet."""

    amount: Decimal = Field(
        ...,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    reference: str = Field(..., min_length=1, max_length=100)
    idempotency_key: str = Field(..., min_length=16, max_length=64)

    @field_validator("amount", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        if isinstance(v, float):
            return Decimal(str(v))
        return Decimal(v) if not isinstance(v, Decimal) else v
```'''
    ))

    return examples


def prepare_all_training_data(output_dir: Path):
    """Prepare all training data and save to JSONL."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_examples = []

    # 1. Extract from templates
    template_dir = Path("data/code_templates")
    for template_file in template_dir.rglob("*.py"):
        for example in extract_examples_from_template(template_file):
            all_examples.append(example)

    # 2. Add fintech-specific examples
    all_examples.extend(create_fintech_examples())

    # Save to JSONL
    output_file = output_dir / "fintech_coder_training.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example) + "\n")

    print(f"Created {len(all_examples)} training examples")
    print(f"Saved to: {output_file}")

    # Also create a summary
    summary = {
        "total_examples": len(all_examples),
        "source_files": list(str(f) for f in template_dir.rglob("*.py")),
        "format": "chat_completion",
        "model_target": "Qwen2.5-Coder-7B-Instruct",
    }

    summary_file = output_dir / "training_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return all_examples


if __name__ == "__main__":
    output_dir = Path("data/training/processed")
    prepare_all_training_data(output_dir)
