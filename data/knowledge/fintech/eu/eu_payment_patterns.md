# EU Payment Patterns and SEPA Integration

## Overview

The Single Euro Payments Area (SEPA) enables standardized euro payments across 36 European countries. Understanding SEPA is essential for EU FinTech development.

## SEPA Payment Schemes

### SEPA Credit Transfer (SCT)
Standard euro transfers, typically next business day.

### SEPA Instant Credit Transfer (SCT Inst)
Real-time transfers, 24/7/365, within 10 seconds.

### SEPA Direct Debit (SDD)
Pull payments with two variants:
- Core (B2C)
- B2B

```python
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
import re

class SEPAScheme(Enum):
    SCT = "sepa_credit_transfer"
    SCT_INST = "sepa_instant"
    SDD_CORE = "sepa_direct_debit_core"
    SDD_B2B = "sepa_direct_debit_b2b"

class SEPATransactionType(Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    RETURN = "return"
    RECALL = "recall"

@dataclass
class SEPAPayment:
    """SEPA payment message"""
    message_id: str
    payment_id: str
    scheme: SEPAScheme
    amount: Decimal
    currency: str  # Always EUR for SEPA
    debtor_name: str
    debtor_iban: str
    debtor_bic: Optional[str]
    creditor_name: str
    creditor_iban: str
    creditor_bic: Optional[str]
    remittance_info: str
    requested_execution_date: date
    end_to_end_id: str

class IBANValidator:
    """Validate and parse IBAN numbers"""

    # IBAN lengths by country
    IBAN_LENGTHS = {
        "DE": 22, "FR": 27, "ES": 24, "IT": 27, "NL": 18,
        "BE": 16, "AT": 20, "PT": 25, "IE": 22, "LU": 20,
        "GB": 22,  # UK still uses IBAN format
    }

    def validate_iban(self, iban: str) -> bool:
        """
        Validate IBAN format and checksum

        Returns True if valid IBAN
        """
        # Remove spaces and convert to uppercase
        iban = iban.replace(" ", "").upper()

        # Check format
        if not re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]+$", iban):
            return False

        # Check length for country
        country = iban[:2]
        expected_length = self.IBAN_LENGTHS.get(country)
        if expected_length and len(iban) != expected_length:
            return False

        # Validate checksum (MOD 97)
        rearranged = iban[4:] + iban[:4]
        numeric = ""
        for char in rearranged:
            if char.isdigit():
                numeric += char
            else:
                numeric += str(ord(char) - 55)

        return int(numeric) % 97 == 1

    def extract_bic(self, iban: str) -> Optional[str]:
        """
        Extract BIC from IBAN (if possible via directory lookup)

        Note: SEPA no longer requires BIC for domestic transfers
        """
        # In real implementation, lookup in SEPA directory
        return None  # BIC lookup would be done via IBAN Plus directory


class SEPACreditTransfer:
    """
    SEPA Credit Transfer (SCT) implementation

    For standard euro transfers across SEPA zone
    """

    MAX_AMOUNT = Decimal("999999999.99")  # SEPA limit
    MAX_REMITTANCE_LENGTH = 140  # Characters

    def __init__(self):
        self.iban_validator = IBANValidator()

    def create_payment(
        self,
        debtor_name: str,
        debtor_iban: str,
        creditor_name: str,
        creditor_iban: str,
        amount: Decimal,
        remittance_info: str,
        requested_date: Optional[date] = None
    ) -> SEPAPayment:
        """
        Create SEPA Credit Transfer payment

        Validates all inputs per SEPA rulebook
        """
        # Validate IBANs
        if not self.iban_validator.validate_iban(debtor_iban):
            raise ValueError("Invalid debtor IBAN")
        if not self.iban_validator.validate_iban(creditor_iban):
            raise ValueError("Invalid creditor IBAN")

        # Validate amount
        if amount <= 0 or amount > self.MAX_AMOUNT:
            raise ValueError(f"Amount must be between 0 and {self.MAX_AMOUNT}")

        # Validate remittance info length
        if len(remittance_info) > self.MAX_REMITTANCE_LENGTH:
            raise ValueError(f"Remittance info max {self.MAX_REMITTANCE_LENGTH} chars")

        # Set execution date
        if requested_date is None:
            requested_date = self._next_business_day()

        return SEPAPayment(
            message_id=self._generate_message_id(),
            payment_id=self._generate_payment_id(),
            scheme=SEPAScheme.SCT,
            amount=amount,
            currency="EUR",
            debtor_name=debtor_name,
            debtor_iban=debtor_iban.replace(" ", "").upper(),
            debtor_bic=None,  # Not required since SEPA end-date
            creditor_name=creditor_name,
            creditor_iban=creditor_iban.replace(" ", "").upper(),
            creditor_bic=None,
            remittance_info=remittance_info[:self.MAX_REMITTANCE_LENGTH],
            requested_execution_date=requested_date,
            end_to_end_id=self._generate_e2e_id()
        )

    def _next_business_day(self) -> date:
        """Get next TARGET2 business day"""
        current = date.today()
        while True:
            current += timedelta(days=1)
            if current.weekday() < 5:  # Mon-Fri
                # Also check TARGET2 holidays
                if current not in self._get_target2_holidays():
                    return current

    def _get_target2_holidays(self) -> list[date]:
        """Get TARGET2 closing days"""
        year = date.today().year
        return [
            date(year, 1, 1),   # New Year
            date(year, 12, 25), # Christmas
            date(year, 12, 26), # Boxing Day
            # Easter Friday and Monday calculated dynamically
        ]


class SEPAInstant:
    """
    SEPA Instant Credit Transfer (SCT Inst)

    Real-time payments 24/7/365, max 10 seconds
    """

    MAX_AMOUNT = Decimal("100000.00")  # Default limit, can be higher
    TIMEOUT_SECONDS = 10

    def __init__(self):
        self.iban_validator = IBANValidator()

    async def create_instant_payment(
        self,
        debtor_name: str,
        debtor_iban: str,
        creditor_name: str,
        creditor_iban: str,
        amount: Decimal,
        remittance_info: str
    ) -> dict:
        """
        Create SEPA Instant payment

        Processes in real-time, 24/7/365
        """
        # Validate amount for instant
        if amount > self.MAX_AMOUNT:
            raise ValueError(f"Amount exceeds instant limit of EUR {self.MAX_AMOUNT}")

        # Check participant reachability
        reachable = await self._check_reachability(creditor_iban)
        if not reachable:
            raise InstantNotAvailableError(
                "Beneficiary bank not reachable for instant payments"
            )

        # Create payment
        payment = SEPAPayment(
            message_id=self._generate_message_id(),
            payment_id=self._generate_payment_id(),
            scheme=SEPAScheme.SCT_INST,
            amount=amount,
            currency="EUR",
            debtor_name=debtor_name,
            debtor_iban=debtor_iban.replace(" ", "").upper(),
            debtor_bic=None,
            creditor_name=creditor_name,
            creditor_iban=creditor_iban.replace(" ", "").upper(),
            creditor_bic=None,
            remittance_info=remittance_info,
            requested_execution_date=date.today(),
            end_to_end_id=self._generate_e2e_id()
        )

        # Execute with timeout
        result = await self._execute_instant(payment)

        return {
            "payment_id": payment.payment_id,
            "status": result["status"],
            "accepted_time": result.get("accepted_time"),
            "processing_time_ms": result.get("processing_time_ms")
        }

    async def _check_reachability(self, iban: str) -> bool:
        """Check if beneficiary bank participates in SCT Inst"""
        # Lookup in SCT Inst directory
        bic = self._iban_to_bic(iban)
        return await self._is_instant_participant(bic)


class SEPADirectDebit:
    """
    SEPA Direct Debit implementation

    Core (B2C) and B2B schemes
    """

    # Lead times
    CORE_FIRST_LEAD_DAYS = 5  # D-5 for first collection (reduced scheme: D-1)
    CORE_RECURRENT_LEAD_DAYS = 2  # D-2 for recurrent (reduced scheme: D-1)
    B2B_LEAD_DAYS = 1  # D-1 for B2B

    # Refund periods
    CORE_REFUND_WEEKS = 8  # 8 weeks no questions asked
    UNAUTHORIZED_REFUND_MONTHS = 13  # 13 months for unauthorized

    @dataclass
    class Mandate:
        """SEPA Direct Debit Mandate"""
        mandate_id: str
        debtor_name: str
        debtor_iban: str
        creditor_id: str
        creditor_name: str
        scheme: str  # CORE or B2B
        signature_date: date
        sequence_type: str  # FRST, RCUR, OOFF, FNAL

    def create_mandate(
        self,
        debtor_name: str,
        debtor_iban: str,
        creditor_id: str,
        creditor_name: str,
        scheme: str = "CORE"
    ) -> "SEPADirectDebit.Mandate":
        """
        Create SEPA Direct Debit Mandate

        Mandate authorizes creditor to collect from debtor's account
        """
        return self.Mandate(
            mandate_id=self._generate_mandate_id(),
            debtor_name=debtor_name,
            debtor_iban=debtor_iban,
            creditor_id=creditor_id,
            creditor_name=creditor_name,
            scheme=scheme,
            signature_date=date.today(),
            sequence_type="FRST"
        )

    def create_collection(
        self,
        mandate: "SEPADirectDebit.Mandate",
        amount: Decimal,
        collection_date: date,
        remittance_info: str
    ) -> dict:
        """
        Create Direct Debit collection

        Validates against mandate and lead times
        """
        # Calculate lead time
        days_until = (collection_date - date.today()).days

        if mandate.scheme == "CORE":
            if mandate.sequence_type == "FRST":
                required_lead = self.CORE_FIRST_LEAD_DAYS
            else:
                required_lead = self.CORE_RECURRENT_LEAD_DAYS
        else:  # B2B
            required_lead = self.B2B_LEAD_DAYS

        if days_until < required_lead:
            raise ValueError(
                f"Collection date must be at least D-{required_lead}"
            )

        return {
            "collection_id": self._generate_collection_id(),
            "mandate_id": mandate.mandate_id,
            "amount": str(amount),
            "collection_date": collection_date.isoformat(),
            "sequence_type": mandate.sequence_type,
            "status": "pending"
        }

    def process_refund(
        self,
        collection_id: str,
        refund_date: date,
        collection_date: date,
        scheme: str,
        authorized: bool = True
    ) -> dict:
        """
        Process Direct Debit refund

        Core: 8 weeks unconditional, 13 months if unauthorized
        B2B: No refund right (except unauthorized)
        """
        weeks_since = (refund_date - collection_date).days / 7

        if scheme == "CORE":
            if authorized and weeks_since <= self.CORE_REFUND_WEEKS:
                return {"status": "approved", "reason": "Within 8-week period"}
            elif not authorized and weeks_since <= self.UNAUTHORIZED_REFUND_MONTHS * 4.3:
                return {"status": "approved", "reason": "Unauthorized collection"}
            else:
                return {"status": "rejected", "reason": "Refund period expired"}
        else:  # B2B
            if not authorized:
                return {"status": "approved", "reason": "Unauthorized collection"}
            else:
                return {"status": "rejected", "reason": "B2B has no refund right"}


class ISO20022Message:
    """
    Generate ISO 20022 XML messages for SEPA

    pain.001 - Customer Credit Transfer Initiation
    pain.002 - Payment Status Report
    pain.008 - Customer Direct Debit Initiation
    """

    def generate_pain001(
        self,
        payments: list[SEPAPayment],
        initiating_party: str
    ) -> str:
        """
        Generate pain.001.001.03 message

        Customer Credit Transfer Initiation
        """
        # Simplified - real implementation uses proper XML library
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>{payments[0].message_id}</MsgId>
      <CreDtTm>{datetime.utcnow().isoformat()}</CreDtTm>
      <NbOfTxs>{len(payments)}</NbOfTxs>
      <CtrlSum>{sum(p.amount for p in payments)}</CtrlSum>
      <InitgPty><Nm>{initiating_party}</Nm></InitgPty>
    </GrpHdr>
    <PmtInf>
      {"".join(self._payment_info(p) for p in payments)}
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""
        return xml

    def _payment_info(self, payment: SEPAPayment) -> str:
        """Generate payment information block"""
        return f"""
      <PmtInfId>{payment.payment_id}</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <ReqdExctnDt>{payment.requested_execution_date}</ReqdExctnDt>
      <Dbtr><Nm>{payment.debtor_name}</Nm></Dbtr>
      <DbtrAcct><Id><IBAN>{payment.debtor_iban}</IBAN></Id></DbtrAcct>
      <CdtTrfTxInf>
        <PmtId><EndToEndId>{payment.end_to_end_id}</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="EUR">{payment.amount}</InstdAmt></Amt>
        <Cdtr><Nm>{payment.creditor_name}</Nm></Cdtr>
        <CdtrAcct><Id><IBAN>{payment.creditor_iban}</IBAN></Id></CdtrAcct>
        <RmtInf><Ustrd>{payment.remittance_info}</Ustrd></RmtInf>
      </CdtTrfTxInf>"""
```

## TARGET2 Integration

```python
from decimal import Decimal
from datetime import datetime, time
from typing import Optional

class TARGET2:
    """
    TARGET2 - Trans-European Automated Real-time Gross Settlement

    For high-value euro payments between banks
    """

    # Operating hours (CET)
    OPENING_TIME = time(7, 0)
    CLOSING_TIME = time(18, 0)
    CUTOFF_CUSTOMER = time(17, 0)

    async def submit_payment(
        self,
        sender_bic: str,
        receiver_bic: str,
        amount: Decimal,
        priority: str = "NORM"  # NORM, URGT, HIGH
    ) -> dict:
        """
        Submit payment to TARGET2

        Real-time gross settlement for large value payments
        """
        # Check operating hours
        if not self._is_open():
            raise TARGET2ClosedError("TARGET2 is closed")

        # Validate participants
        await self._validate_participants(sender_bic, receiver_bic)

        # Submit for settlement
        result = await self._submit_for_settlement(
            sender=sender_bic,
            receiver=receiver_bic,
            amount=amount,
            priority=priority
        )

        return {
            "reference": result["reference"],
            "status": result["status"],
            "settlement_time": result.get("settlement_time"),
            "amount": str(amount)
        }

    def _is_open(self) -> bool:
        """Check if TARGET2 is currently open"""
        now = datetime.now().time()
        today = datetime.now().date()

        # Check if business day
        if today.weekday() >= 5:
            return False

        # Check operating hours
        return self.OPENING_TIME <= now <= self.CLOSING_TIME
```
