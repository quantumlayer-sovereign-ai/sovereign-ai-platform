# PSD2 and Strong Customer Authentication

## Overview

The Payment Services Directive 2 (PSD2) regulates payment services in the EU. A key requirement is Strong Customer Authentication (SCA), mandated by the Regulatory Technical Standards (RTS).

## Strong Customer Authentication (SCA)

SCA requires authentication using at least 2 of 3 independent factors:

1. **Knowledge** - Something only the user knows (password, PIN)
2. **Possession** - Something only the user possesses (phone, token)
3. **Inherence** - Something the user is (biometrics)

### SCA Requirements

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import secrets

class AuthFactor(Enum):
    KNOWLEDGE = "knowledge"      # Password, PIN
    POSSESSION = "possession"    # Phone, hardware token
    INHERENCE = "inherence"      # Biometrics

@dataclass
class SCAResult:
    """Result of SCA verification"""
    verified: bool
    factors_used: list[AuthFactor]
    auth_code: str
    linked_amount: Optional[float] = None
    linked_payee: Optional[str] = None
    timestamp: datetime = None

class StrongCustomerAuth:
    """
    PSD2 Strong Customer Authentication implementation

    Ensures 2 of 3 factors from different categories
    """

    def verify_sca(
        self,
        knowledge_verified: bool = False,
        possession_verified: bool = False,
        inherence_verified: bool = False,
        amount: Optional[float] = None,
        payee: Optional[str] = None
    ) -> SCAResult:
        """
        Verify Strong Customer Authentication

        Must have at least 2 independent factors from different categories
        """
        factors_used = []

        if knowledge_verified:
            factors_used.append(AuthFactor.KNOWLEDGE)
        if possession_verified:
            factors_used.append(AuthFactor.POSSESSION)
        if inherence_verified:
            factors_used.append(AuthFactor.INHERENCE)

        # Require at least 2 factors
        verified = len(factors_used) >= 2

        # Generate dynamic auth code linked to transaction
        auth_code = self._generate_dynamic_auth_code(amount, payee)

        return SCAResult(
            verified=verified,
            factors_used=factors_used,
            auth_code=auth_code,
            linked_amount=amount,
            linked_payee=payee,
            timestamp=datetime.utcnow()
        )

    def _generate_dynamic_auth_code(
        self,
        amount: Optional[float],
        payee: Optional[str]
    ) -> str:
        """
        Generate authentication code dynamically linked to transaction

        PSD2 Article 97(2) - Dynamic linking requirement
        """
        # Include transaction details in code generation
        link_data = f"{amount or 0}:{payee or 'none'}:{secrets.token_hex(8)}"
        return secrets.token_hex(16)


class SCAExemptionChecker:
    """
    Check and apply SCA exemptions per RTS Articles 10-18

    Exemptions can reduce friction for low-risk transactions
    """

    # RTS Article 16 - Low value transactions
    LOW_VALUE_LIMIT = 30.00  # EUR
    LOW_VALUE_CUMULATIVE = 100.00  # EUR
    LOW_VALUE_COUNT = 5

    # RTS Article 18 - Transaction Risk Analysis thresholds
    TRA_THRESHOLDS = {
        500: 0.13,   # Up to €500, max 13 bps fraud rate
        250: 0.06,   # Up to €250, max 6 bps fraud rate
        100: 0.01,   # Up to €100, max 1 bp fraud rate
    }

    def check_low_value_exemption(
        self,
        amount: float,
        cumulative_amount: float,
        transaction_count: int
    ) -> bool:
        """
        Check if low-value exemption applies (RTS Article 16)

        Limits: €30 per transaction, €100 cumulative, 5 transactions
        """
        if amount > self.LOW_VALUE_LIMIT:
            return False

        if cumulative_amount + amount > self.LOW_VALUE_CUMULATIVE:
            return False

        if transaction_count >= self.LOW_VALUE_COUNT:
            return False

        return True

    def check_tra_exemption(
        self,
        amount: float,
        fraud_score: float,
        psp_fraud_rate: float
    ) -> bool:
        """
        Check if Transaction Risk Analysis exemption applies (RTS Article 18)

        Based on fraud rates and transaction amount
        """
        for threshold, max_rate in sorted(
            self.TRA_THRESHOLDS.items(), reverse=True
        ):
            if amount <= threshold:
                if psp_fraud_rate <= max_rate and fraud_score < 0.5:
                    return True
        return False

    def check_trusted_beneficiary(
        self,
        payee_id: str,
        trusted_list: list[str]
    ) -> bool:
        """
        Check if trusted beneficiary exemption applies (RTS Article 13)

        Payee must be on customer's trusted list (added with SCA)
        """
        return payee_id in trusted_list

    def check_recurring_exemption(
        self,
        payee_id: str,
        amount: float,
        first_payment_sca: bool,
        previous_amount: float
    ) -> bool:
        """
        Check if recurring payment exemption applies (RTS Article 14)

        Same amount, same payee, SCA on first payment
        """
        if not first_payment_sca:
            return False

        # Amount must be same (or within tolerance for subscriptions)
        return abs(amount - previous_amount) < 0.01
```

## Dynamic Linking

Authentication codes must be dynamically linked to:
- Transaction amount
- Payee identity

```python
import hmac
import hashlib
from datetime import datetime

class DynamicLinking:
    """
    Implement PSD2 dynamic linking requirement

    Auth code must be linked to specific amount and payee
    Changing either invalidates the code
    """

    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key

    def generate_linked_auth_code(
        self,
        transaction_id: str,
        amount: float,
        payee_account: str,
        currency: str = "EUR"
    ) -> str:
        """
        Generate authentication code linked to transaction details

        Any modification to amount or payee will invalidate the code
        """
        # Create message from transaction details
        message = f"{transaction_id}|{amount:.2f}|{currency}|{payee_account}|{datetime.utcnow().isoformat()}"

        # Generate HMAC
        auth_code = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:12].upper()

        return auth_code

    def verify_linked_auth_code(
        self,
        auth_code: str,
        transaction_id: str,
        amount: float,
        payee_account: str,
        currency: str = "EUR",
        timestamp: str = None
    ) -> bool:
        """
        Verify that auth code matches transaction details

        Returns False if amount or payee has been modified
        """
        # Regenerate and compare
        expected = self.generate_linked_auth_code(
            transaction_id, amount, payee_account, currency
        )
        return hmac.compare_digest(auth_code, expected)
```

## Open Banking APIs

PSD2 requires banks (ASPSPs) to provide API access to Third Party Providers (TPPs).

### TPP Types

- **AISP** - Account Information Service Provider
- **PISP** - Payment Initiation Service Provider
- **CBPII** - Card-Based Payment Instrument Issuer

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import requests

class TPPType(Enum):
    AISP = "aisp"
    PISP = "pisp"
    CBPII = "cbpii"

@dataclass
class TPPCredential:
    """TPP credential with eIDAS certificate"""
    tpp_id: str
    qwac_certificate: str  # Qualified Website Authentication Certificate
    tpp_type: TPPType
    national_competent_authority: str
    authorization_number: str

class OpenBankingAPI:
    """
    PSD2 Open Banking API implementation

    Provides account information and payment initiation for TPPs
    """

    async def verify_tpp_certificate(
        self,
        qwac_certificate: str
    ) -> TPPCredential:
        """
        Verify TPP's eIDAS QWAC certificate

        Check against EBA register and validate certificate chain
        """
        # Parse certificate
        tpp_info = self._parse_qwac(qwac_certificate)

        # Verify against EBA TPP register
        registered = await self._check_eba_register(tpp_info["authorization_number"])
        if not registered:
            raise UnauthorizedTPPError("TPP not found in EBA register")

        return TPPCredential(**tpp_info)

    async def get_account_info(
        self,
        tpp: TPPCredential,
        consent_id: str,
        account_id: str
    ) -> dict:
        """
        Provide account information to authorized AISP

        Requires valid consent and AISP authorization
        """
        if tpp.tpp_type not in [TPPType.AISP]:
            raise UnauthorizedTPPError("TPP not authorized for account access")

        # Verify consent is valid
        consent = await self._verify_consent(consent_id, account_id)
        if not consent.is_valid():
            raise ConsentExpiredError("Consent has expired or been revoked")

        # Return account data per consent scope
        return await self._fetch_account_data(account_id, consent.scope)

    async def initiate_payment(
        self,
        tpp: TPPCredential,
        payment_request: dict
    ) -> dict:
        """
        Initiate payment on behalf of PSU

        Requires PISP authorization and SCA from PSU
        """
        if tpp.tpp_type not in [TPPType.PISP]:
            raise UnauthorizedTPPError("TPP not authorized for payment initiation")

        # Create payment initiation
        payment_id = await self._create_payment(payment_request)

        # Return with SCA redirect
        return {
            "payment_id": payment_id,
            "status": "requires_sca",
            "sca_redirect_url": f"/sca/authorize/{payment_id}",
            "sca_methods": ["redirect", "decoupled"]
        }
```

## Consent Management

```python
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class ConsentScope(Enum):
    ACCOUNTS = "accounts"
    BALANCES = "balances"
    TRANSACTIONS = "transactions"

@dataclass
class PSD2Consent:
    """PSD2 account access consent"""
    consent_id: str
    tpp_id: str
    psu_id: str
    accounts: list[str]
    scope: list[ConsentScope]
    valid_until: datetime
    frequency_per_day: int = 4
    recurring: bool = True
    created_at: datetime = None

    def is_valid(self) -> bool:
        return datetime.utcnow() < self.valid_until

class ConsentManager:
    """Manage PSD2 consent lifecycle"""

    MAX_CONSENT_VALIDITY_DAYS = 90

    async def create_consent(
        self,
        tpp_id: str,
        psu_id: str,
        accounts: list[str],
        scope: list[ConsentScope]
    ) -> PSD2Consent:
        """
        Create new account access consent

        Max validity 90 days, requires SCA at creation
        """
        consent = PSD2Consent(
            consent_id=self._generate_consent_id(),
            tpp_id=tpp_id,
            psu_id=psu_id,
            accounts=accounts,
            scope=scope,
            valid_until=datetime.utcnow() + timedelta(days=self.MAX_CONSENT_VALIDITY_DAYS),
            created_at=datetime.utcnow()
        )

        await self._store_consent(consent)
        return consent

    async def revoke_consent(self, consent_id: str) -> bool:
        """Revoke consent - must be effective immediately"""
        return await self._delete_consent(consent_id)
```

## Refund Rights (Article 73)

```python
from datetime import datetime
from decimal import Decimal

class PSD2RefundHandler:
    """Handle PSD2 refund rights"""

    MAX_LIABILITY_UNAUTHORIZED = Decimal("50.00")  # EUR

    async def process_unauthorized_refund(
        self,
        transaction_id: str,
        user_id: str,
        report_date: datetime
    ) -> dict:
        """
        Process refund for unauthorized transaction

        User liability limited to €50 unless gross negligence
        """
        transaction = await self._get_transaction(transaction_id)

        # Check 13-month notification limit
        if (datetime.utcnow() - transaction.date).days > 395:
            return {"status": "rejected", "reason": "Notification period exceeded"}

        # Immediate refund required
        refund_amount = transaction.amount
        user_liability = min(self.MAX_LIABILITY_UNAUTHORIZED, refund_amount)

        refund = await self._create_refund(
            transaction_id=transaction_id,
            amount=refund_amount - user_liability,
            reason="unauthorized_transaction"
        )

        return {
            "status": "completed",
            "refund_id": refund.id,
            "refunded_amount": str(refund_amount - user_liability),
            "user_liability": str(user_liability)
        }
```
