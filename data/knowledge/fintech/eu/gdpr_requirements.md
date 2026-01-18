# GDPR Requirements for FinTech

## Overview

The General Data Protection Regulation (EU) 2016/679 is the primary data protection law in the European Union. For FinTech applications, GDPR compliance is critical as financial services process significant amounts of personal data.

## Key Principles (Article 5)

### 1. Lawfulness, Fairness, and Transparency
Personal data must be processed lawfully, fairly, and in a transparent manner.

### 2. Purpose Limitation
Data collected for specified, explicit, and legitimate purposes must not be processed incompatibly.

### 3. Data Minimization
Personal data must be adequate, relevant, and limited to what is necessary.

### 4. Accuracy
Personal data must be accurate and kept up to date.

### 5. Storage Limitation
Personal data must be kept no longer than necessary.

### 6. Integrity and Confidentiality
Personal data must be processed with appropriate security.

## Lawful Basis for Processing (Article 6)

For FinTech, common lawful bases include:

1. **Contract Performance** - Processing necessary for payment execution
2. **Legal Obligation** - AML/KYC requirements
3. **Legitimate Interests** - Fraud prevention
4. **Consent** - Marketing communications

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class LawfulBasis(Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

@dataclass
class ProcessingRecord:
    """Record of lawful basis for processing"""
    purpose: str
    lawful_basis: LawfulBasis
    data_categories: list[str]
    retention_period: str
    documented_at: datetime

def verify_lawful_basis(processing_purpose: str) -> LawfulBasis:
    """Verify and return lawful basis for a processing activity"""
    # Example mapping
    purpose_mapping = {
        "payment_processing": LawfulBasis.CONTRACT,
        "aml_verification": LawfulBasis.LEGAL_OBLIGATION,
        "fraud_detection": LawfulBasis.LEGITIMATE_INTERESTS,
        "marketing": LawfulBasis.CONSENT,
    }
    return purpose_mapping.get(processing_purpose, LawfulBasis.CONSENT)
```

## Data Subject Rights

### Right to Access (Article 15)
Data subjects can request copies of their personal data.

### Right to Rectification (Article 16)
Data subjects can request correction of inaccurate data.

### Right to Erasure (Article 17)
The "right to be forgotten" - data subjects can request deletion.

```python
import json
from datetime import datetime
from typing import Optional

class GDPRDataSubjectService:
    """Service for handling GDPR data subject requests"""

    async def handle_access_request(
        self,
        user_id: str,
        request_id: str
    ) -> dict:
        """
        Handle Article 15 access request

        Must respond within 1 month (extendable to 3 months for complex requests)
        """
        # Collect all personal data
        personal_data = await self._collect_user_data(user_id)

        # Log the request for audit
        await self._log_dsr_request(
            request_type="access",
            user_id=user_id,
            request_id=request_id
        )

        return {
            "request_id": request_id,
            "data": personal_data,
            "generated_at": datetime.utcnow().isoformat(),
            "format": "json"
        }

    async def handle_erasure_request(
        self,
        user_id: str,
        request_id: str
    ) -> dict:
        """
        Handle Article 17 erasure request

        Must delete data unless legal retention applies
        """
        # Check for legal holds
        legal_hold = await self._check_legal_retention(user_id)
        if legal_hold:
            return {
                "request_id": request_id,
                "status": "partially_completed",
                "reason": "Legal retention requirements apply to some data"
            }

        # Delete from all systems
        await self._delete_user_data(user_id)

        # Propagate to processors
        await self._notify_processors_of_deletion(user_id)

        return {
            "request_id": request_id,
            "status": "completed",
            "deleted_at": datetime.utcnow().isoformat()
        }

    async def export_user_data(
        self,
        user_id: str,
        format: str = "json"
    ) -> bytes:
        """
        Handle Article 20 data portability request

        Provide data in machine-readable format
        """
        data = await self._collect_user_data(user_id)

        if format == "json":
            return json.dumps(data, indent=2).encode()
        elif format == "csv":
            return self._to_csv(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
```

## Breach Notification (Article 33)

Personal data breaches must be reported to the supervisory authority within 72 hours.

```python
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger()

class BreachSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class GDPRBreachHandler:
    """Handle GDPR breach notification requirements"""

    NOTIFICATION_DEADLINE_HOURS = 72

    async def report_breach(
        self,
        breach_description: str,
        data_categories: list[str],
        affected_count: int,
        severity: BreachSeverity
    ) -> dict:
        """
        Report personal data breach

        Must notify DPA within 72 hours unless unlikely to result in risk
        """
        breach_id = self._generate_breach_id()
        discovered_at = datetime.utcnow()
        deadline = discovered_at + timedelta(hours=self.NOTIFICATION_DEADLINE_HOURS)

        # Log immediately
        logger.critical(
            "personal_data_breach_detected",
            breach_id=breach_id,
            severity=severity.value,
            affected_count=affected_count,
            notification_deadline=deadline.isoformat()
        )

        # Assess if notification required (risk to individuals)
        requires_notification = self._assess_notification_requirement(
            severity, data_categories, affected_count
        )

        if requires_notification:
            # Queue notification to DPA
            await self._queue_dpa_notification(
                breach_id=breach_id,
                deadline=deadline,
                details={
                    "description": breach_description,
                    "categories": data_categories,
                    "affected_count": affected_count
                }
            )

            # If high risk, notify affected individuals (Article 34)
            if severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]:
                await self._notify_affected_individuals(breach_id)

        return {
            "breach_id": breach_id,
            "discovered_at": discovered_at.isoformat(),
            "notification_deadline": deadline.isoformat(),
            "requires_dpa_notification": requires_notification
        }
```

## Data Protection by Design (Article 25)

Implement privacy by design principles:

```python
from cryptography.fernet import Fernet
import hashlib
import secrets

class PrivacyByDesign:
    """Implement GDPR Article 25 - Data Protection by Design"""

    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def pseudonymize(self, personal_data: str) -> tuple[str, str]:
        """
        Pseudonymize personal data

        Returns pseudonym and securely stored mapping
        """
        # Generate random pseudonym
        pseudonym = secrets.token_hex(16)

        # Store mapping securely (encrypted)
        mapping = self.cipher.encrypt(personal_data.encode())

        return pseudonym, mapping.decode()

    def anonymize(self, dataset: list[dict]) -> list[dict]:
        """
        Anonymize dataset - irreversible

        Applies k-anonymity and removes direct identifiers
        """
        anonymized = []
        for record in dataset:
            anon_record = {
                k: v for k, v in record.items()
                if k not in ["name", "email", "phone", "address", "national_id"]
            }
            # Generalize quasi-identifiers
            if "age" in anon_record:
                anon_record["age_range"] = self._generalize_age(anon_record.pop("age"))
            if "postcode" in anon_record:
                anon_record["region"] = anon_record.pop("postcode")[:3]

            anonymized.append(anon_record)

        return anonymized

    def encrypt_pii(self, data: str) -> str:
        """Encrypt personal data at rest"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_pii(self, encrypted_data: str) -> str:
        """Decrypt personal data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

## International Transfers (Articles 44-49)

Data transfers outside the EU/EEA require appropriate safeguards:

- Standard Contractual Clauses (SCCs)
- Binding Corporate Rules (BCRs)
- Adequacy decisions
- Derogations for specific situations

```python
from enum import Enum

class TransferMechanism(Enum):
    ADEQUACY = "adequacy_decision"
    SCC = "standard_contractual_clauses"
    BCR = "binding_corporate_rules"
    DEROGATION = "derogation"

ADEQUATE_COUNTRIES = [
    "UK", "Switzerland", "Japan", "South Korea",
    "Canada", "Argentina", "Israel", "New Zealand"
]

def validate_international_transfer(
    destination_country: str,
    transfer_mechanism: TransferMechanism | None = None
) -> bool:
    """
    Validate international data transfer compliance

    Returns True if transfer is compliant
    """
    # EU/EEA countries - no restriction
    if destination_country in ["EU", "EEA"]:
        return True

    # Check adequacy decision
    if destination_country in ADEQUATE_COUNTRIES:
        return True

    # Require appropriate safeguards
    if transfer_mechanism in [TransferMechanism.SCC, TransferMechanism.BCR]:
        return True

    return False
```

## Record of Processing Activities (Article 30)

Maintain records of all processing activities:

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProcessingActivity:
    """ROPA entry per Article 30"""
    name: str
    purpose: str
    lawful_basis: str
    data_categories: list[str]
    data_subjects: list[str]
    recipients: list[str]
    transfers: list[str]
    retention_period: str
    security_measures: list[str]
    dpia_required: bool = False
    last_reviewed: datetime = None

# Example ROPA for payment processing
payment_processing_ropa = ProcessingActivity(
    name="Payment Transaction Processing",
    purpose="Execute customer payment instructions",
    lawful_basis="Contract performance (Article 6(1)(b))",
    data_categories=["Name", "IBAN", "Transaction amount", "Payment reference"],
    data_subjects=["Customers", "Payees"],
    recipients=["Payment processor", "Receiving bank"],
    transfers=["SEPA network (EU)"],
    retention_period="7 years (legal obligation)",
    security_measures=["Encryption", "Access control", "Audit logging"],
    dpia_required=False
)
```
