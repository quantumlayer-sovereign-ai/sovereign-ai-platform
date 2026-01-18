"""
Coder Generator - Code Generation Training Data

Generates training samples for the fintech_coder role focusing on:
- Payment API implementation
- UPI/banking code patterns
- Secure coding practices
"""

import re
from .base import BaseGenerator, TrainingSample


class CoderGenerator(BaseGenerator):
    """Generator for fintech_coder role"""

    def __init__(self):
        super().__init__()
        self.role_name = "fintech_coder"
        self.focus_areas = ["code_generation", "api_patterns", "secure_coding"]
        self.compliance_tags = ["pci_dss", "rbi"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate code-focused training samples"""
        samples = []

        # Extract code blocks for code generation samples
        samples.extend(self._generate_code_samples(content, source_file))

        # Generate function implementation samples
        samples.extend(self._generate_implementation_samples(content, source_file))

        # Generate secure coding samples
        samples.extend(self._generate_secure_coding_samples(content, source_file))

        return samples

    def _generate_code_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate samples from code blocks"""
        samples = []
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code = block["code"]

            # Extract class definitions
            class_match = re.search(r"class\s+(\w+).*?:", code)
            if class_match:
                class_name = class_match.group(1)
                docstring = self._extract_docstring(code)

                if docstring:
                    samples.append(self.create_sample(
                        instruction=f"Implement a Python class called {class_name} for payment processing",
                        input_text=docstring,
                        output=code,
                        category="class_implementation",
                        source_file=source_file
                    ))

            # Extract function definitions
            func_matches = re.findall(
                r"(def\s+(\w+)\s*\([^)]*\)[^:]*:.*?)(?=\ndef\s|\nclass\s|\Z)",
                code,
                re.DOTALL
            )

            for func_code, func_name in func_matches:
                if func_name.startswith("_") and not func_name.startswith("__"):
                    continue  # Skip private methods for now

                docstring = self._extract_function_docstring(func_code)
                if docstring:
                    samples.append(self.create_sample(
                        instruction=f"Write a Python function called `{func_name}` for FinTech application",
                        input_text=docstring,
                        output=func_code.strip(),
                        category="function_implementation",
                        source_file=source_file
                    ))

        return samples

    def _generate_implementation_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate implementation-focused samples"""
        samples = []
        sections = self.extract_sections(content)

        # Create implementation samples from pattern descriptions
        implementation_keywords = [
            "implementation", "example", "code", "pattern", "handler",
            "processor", "service", "manager"
        ]

        for section_name, section_content in sections.items():
            if not any(kw in section_name for kw in implementation_keywords):
                continue

            code_blocks = self.extract_code_blocks(section_content)
            if not code_blocks:
                continue

            # Use section content before code as description
            description = re.split(r"```", section_content)[0].strip()
            if len(description) < 20:
                continue

            for block in code_blocks:
                if block["language"] == "python":
                    # Create various instruction formats
                    samples.extend(self._create_implementation_variants(
                        description, block["code"], section_name, source_file
                    ))

        return samples

    def _generate_secure_coding_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate secure coding practice samples"""
        samples = []

        # Look for security-related patterns
        security_patterns = [
            ("sql injection", "PCI-6.3"),
            ("xss", "PCI-6.3"),
            ("encryption", "PCI-3.4"),
            ("authentication", "PCI-8"),
            ("session", "PCI-8"),
            ("password", "PCI-8.2"),
            ("token", "PCI-3.4"),
            ("mask", "PCI-3.3"),
        ]

        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code = block["code"]
            code_lower = code.lower()

            for pattern, pci_req in security_patterns:
                if pattern in code_lower:
                    # Create security-focused samples
                    samples.append(self.create_sample(
                        instruction=f"Write secure Python code that handles {pattern.replace('_', ' ')} properly for a FinTech application",
                        input_text=f"Ensure compliance with {pci_req}",
                        output=code,
                        category="secure_coding",
                        compliance_tags=[pci_req],
                        source_file=source_file
                    ))
                    break

        return samples

    def _create_implementation_variants(
        self, description: str, code: str, context: str, source_file: str
    ) -> list[TrainingSample]:
        """Create multiple instruction variants for same code"""
        samples = []

        # Clean description
        desc_clean = re.sub(r"\s+", " ", description[:200]).strip()

        # Variant 1: Direct implementation request
        samples.append(self.create_sample(
            instruction=f"Implement the following FinTech functionality in Python: {desc_clean}",
            output=code,
            category="implementation",
            source_file=source_file
        ))

        # Variant 2: With context
        samples.append(self.create_sample(
            instruction=f"Write Python code for a payment system",
            input_text=desc_clean,
            output=code,
            category="implementation",
            source_file=source_file
        ))

        return samples

    def _extract_docstring(self, code: str) -> str:
        """Extract docstring from code"""
        match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r"'''(.*?)'''", code, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_function_docstring(self, func_code: str) -> str:
        """Extract docstring from function"""
        lines = func_code.split("\n")
        in_docstring = False
        docstring_lines = []

        for line in lines[1:]:  # Skip def line
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    # End of docstring
                    break
                else:
                    in_docstring = True
                    # Check if single-line docstring
                    if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        return stripped.strip("\"'")
            elif in_docstring:
                docstring_lines.append(stripped)

        return " ".join(docstring_lines).strip()

    def generate_payment_api_samples(self) -> list[TrainingSample]:
        """Generate synthetic payment API samples"""
        samples = []

        # Payment gateway integration
        samples.append(self.create_sample(
            instruction="Write a Python function to process a payment using Razorpay",
            input_text="The function should handle amount in INR, customer email, and return payment status",
            output='''async def process_razorpay_payment(
    amount: Decimal,
    customer_email: str,
    order_id: str
) -> dict:
    """
    Process payment using Razorpay gateway

    Args:
        amount: Payment amount in INR (Decimal to avoid float errors)
        customer_email: Customer's email for receipt
        order_id: Unique order identifier

    Returns:
        Payment status dictionary
    """
    import razorpay
    import os

    # Never hardcode credentials
    client = razorpay.Client(
        auth=(os.environ["RAZORPAY_KEY_ID"], os.environ["RAZORPAY_SECRET"])
    )

    # Convert to smallest unit (paisa)
    amount_paisa = int(amount * 100)

    try:
        payment = client.order.create({
            "amount": amount_paisa,
            "currency": "INR",
            "receipt": order_id,
            "payment_capture": 1,  # Auto-capture
            "notes": {
                "customer_email": customer_email  # Don't log PII
            }
        })

        # Audit log (no sensitive data)
        logger.info("payment_initiated",
                   order_id=order_id,
                   amount_paisa=amount_paisa,
                   razorpay_order_id=payment["id"])

        return {
            "status": "created",
            "order_id": payment["id"],
            "amount": str(amount)
        }

    except razorpay.errors.BadRequestError as e:
        logger.error("payment_failed", order_id=order_id, error=str(e))
        raise PaymentError(f"Payment creation failed: {e}")''',
            category="payment_api",
            compliance_tags=["PCI-6", "PCI-10"]
        ))

        # UPI payment
        samples.append(self.create_sample(
            instruction="Implement a UPI payment handler with proper validation",
            input_text="Handle UPI ID validation, amount limits, and transaction status",
            output='''import re
from decimal import Decimal
from typing import Optional

class UPIPaymentHandler:
    """Handle UPI payments with validation and compliance"""

    UPI_REGEX = r"^[a-zA-Z0-9._-]+@[a-zA-Z]{3,}$"
    MAX_AMOUNT = Decimal("100000")  # RBI UPI limit
    MIN_AMOUNT = Decimal("1")

    async def validate_upi_id(self, upi_id: str) -> bool:
        """Validate UPI ID format"""
        if not re.match(self.UPI_REGEX, upi_id):
            raise ValidationError("Invalid UPI ID format")
        return True

    async def initiate_payment(
        self,
        payer_upi: str,
        payee_upi: str,
        amount: Decimal,
        remarks: str = ""
    ) -> dict:
        """
        Initiate UPI payment

        Args:
            payer_upi: Payer's UPI ID
            payee_upi: Payee's UPI ID
            amount: Amount in INR (Decimal)
            remarks: Transaction remarks

        Returns:
            Transaction status
        """
        # Validate inputs
        await self.validate_upi_id(payer_upi)
        await self.validate_upi_id(payee_upi)

        if not self.MIN_AMOUNT <= amount <= self.MAX_AMOUNT:
            raise ValidationError(
                f"Amount must be between {self.MIN_AMOUNT} and {self.MAX_AMOUNT}"
            )

        # Generate unique transaction ID
        txn_id = self._generate_txn_id()

        # Create audit log before transaction
        audit_logger.log_transaction_initiated(
            txn_id=txn_id,
            amount=str(amount),
            payer_masked=self._mask_upi(payer_upi),
            payee_masked=self._mask_upi(payee_upi)
        )

        # Call UPI switch (PSP API)
        response = await self._call_psp_api(
            txn_id=txn_id,
            payer=payer_upi,
            payee=payee_upi,
            amount=int(amount * 100),  # Convert to paisa
            remarks=remarks[:50]  # Limit remarks length
        )

        return {
            "txn_id": txn_id,
            "status": response["status"],
            "amount": str(amount)
        }

    def _mask_upi(self, upi_id: str) -> str:
        """Mask UPI ID for logging"""
        parts = upi_id.split("@")
        if len(parts) == 2:
            masked = parts[0][:2] + "***" + "@" + parts[1]
            return masked
        return "***@***"

    def _generate_txn_id(self) -> str:
        """Generate unique transaction ID"""
        import uuid
        from datetime import datetime
        return f"UPI{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"''',
            category="upi_payment",
            compliance_tags=["RBI-UPI", "PCI-10"]
        ))

        return samples
