# UK Payment Patterns

## Overview

The UK has a well-developed payment infrastructure with several key schemes:
- Faster Payments Service (FPS) - Real-time payments
- BACS - Bulk payments and Direct Debits
- CHAPS - High-value same-day payments
- Card schemes (Visa, Mastercard)

## Faster Payments Service

```python
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

class FPSStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    SETTLED = "settled"
    REJECTED = "rejected"
    RETURNED = "returned"

@dataclass
class FPSPayment:
    """Faster Payments Service payment"""
    payment_id: str
    sender_sort_code: str
    sender_account: str
    recipient_sort_code: str
    recipient_account: str
    amount: Decimal
    reference: str
    status: FPSStatus
    created_at: datetime
    settled_at: Optional[datetime] = None

class FasterPayments:
    """
    UK Faster Payments Service implementation

    Real-time payments 24/7/365
    """

    # FPS limits (can vary by participant)
    DEFAULT_SINGLE_LIMIT = Decimal("1000000")  # £1M
    DEFAULT_DAILY_LIMIT = Decimal("5000000")   # £5M

    # Processing time SLA
    TARGET_SECONDS = 10  # 99% within 10 seconds

    def __init__(self):
        self.single_limit = self.DEFAULT_SINGLE_LIMIT
        self.daily_limit = self.DEFAULT_DAILY_LIMIT

    async def submit_payment(
        self,
        sender_sort_code: str,
        sender_account: str,
        recipient_sort_code: str,
        recipient_account: str,
        amount: Decimal,
        reference: str
    ) -> FPSPayment:
        """
        Submit Faster Payment

        Processed in near real-time
        """
        # Validate sort codes
        self._validate_sort_code(sender_sort_code)
        self._validate_sort_code(recipient_sort_code)

        # Check amount limits
        if amount > self.single_limit:
            raise ValueError(
                f"Amount exceeds FPS limit of £{self.single_limit}"
            )

        # Check recipient reachability
        reachable = await self._check_fps_reachability(
            recipient_sort_code
        )
        if not reachable:
            raise FPSNotReachableError(
                "Recipient bank not reachable via FPS"
            )

        # Create payment
        payment = FPSPayment(
            payment_id=self._generate_payment_id(),
            sender_sort_code=sender_sort_code,
            sender_account=sender_account,
            recipient_sort_code=recipient_sort_code,
            recipient_account=recipient_account,
            amount=amount,
            reference=reference[:18],  # FPS reference limit
            status=FPSStatus.PENDING,
            created_at=datetime.utcnow()
        )

        # Submit for processing
        result = await self._submit_to_fps(payment)

        payment.status = FPSStatus.ACCEPTED if result["accepted"] else FPSStatus.REJECTED

        return payment

    async def health_check(self) -> dict:
        """
        FPS health and availability check
        """
        # Check FPS infrastructure status
        fps_status = await self._check_fps_status()

        return {
            "available": fps_status["available"],
            "latency_ms": fps_status["latency"],
            "last_successful_payment": fps_status["last_success"],
            "pending_queue_size": fps_status["queue_size"]
        }

    async def monitor_availability(
        self,
        period_hours: int = 24
    ) -> dict:
        """
        Monitor FPS availability metrics

        PSR requires 99.7% availability
        """
        metrics = await self._get_availability_metrics(period_hours)

        return {
            "period_hours": period_hours,
            "availability_percent": metrics["availability"],
            "total_minutes": period_hours * 60,
            "downtime_minutes": metrics["downtime"],
            "meets_sla": metrics["availability"] >= 99.7,
            "incidents": metrics["incidents"]
        }

    def service_status(self) -> dict:
        """Current service status"""
        return {
            "service": "faster_payments",
            "status": "operational",
            "limits": {
                "single_payment": str(self.single_limit),
                "daily": str(self.daily_limit)
            },
            "checked_at": datetime.utcnow().isoformat()
        }

    def _validate_sort_code(self, sort_code: str):
        """Validate UK sort code format"""
        import re
        clean = sort_code.replace("-", "").replace(" ", "")
        if not re.match(r"^\d{6}$", clean):
            raise ValueError(f"Invalid sort code: {sort_code}")


class FPSReturns:
    """Handle FPS payment returns"""

    RETURN_REASONS = {
        "ACCOUNT_CLOSED": "Account closed",
        "INVALID_ACCOUNT": "Invalid account number",
        "BENEFICIARY_DECEASED": "Beneficiary deceased",
        "CREDIT_REFUSED": "Credit refused by beneficiary",
        "REFER_TO_ORIGINATOR": "Refer to originator"
    }

    async def process_return(
        self,
        original_payment_id: str,
        return_reason: str
    ) -> dict:
        """
        Process FPS return

        Credit funds back to sender
        """
        original = await self._get_payment(original_payment_id)

        # Create return payment
        return_payment = await self._create_return(
            original=original,
            reason=return_reason
        )

        return {
            "return_id": return_payment["id"],
            "original_payment_id": original_payment_id,
            "amount": str(original.amount),
            "reason": self.RETURN_REASONS.get(return_reason, return_reason),
            "status": "completed"
        }
```

## BACS Payments

```python
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

class BACSType(Enum):
    DIRECT_CREDIT = "direct_credit"
    DIRECT_DEBIT = "direct_debit"

class BACSSequence(Enum):
    FIRST = "first"
    RECURRING = "recurring"
    FINAL = "final"
    ONE_OFF = "one_off"

@dataclass
class BACSInstruction:
    """BACS payment instruction"""
    instruction_id: str
    instruction_type: BACSType
    originator_sort_code: str
    originator_account: str
    destination_sort_code: str
    destination_account: str
    amount: Decimal
    reference: str
    processing_date: date
    service_user_number: str

class BACSPayments:
    """
    BACS Payment Service implementation

    3-day processing cycle for bulk payments
    """

    # BACS cycle: Input day, Processing day, Entry day
    PROCESSING_DAYS = 3

    def submit_bacs(
        self,
        instructions: list[BACSInstruction]
    ) -> dict:
        """
        Submit BACS file for processing

        3-day cycle: D-2 input, D-1 processing, D entry
        """
        # Group by processing date
        by_date = {}
        for inst in instructions:
            proc_date = str(inst.processing_date)
            if proc_date not in by_date:
                by_date[proc_date] = []
            by_date[proc_date].append(inst)

        # Generate BACS files
        files = []
        for proc_date, insts in by_date.items():
            bacs_file = self._generate_bacs_file(insts)
            files.append({
                "processing_date": proc_date,
                "instruction_count": len(insts),
                "total_value": str(sum(i.amount for i in insts)),
                "file_reference": bacs_file["reference"]
            })

        return {
            "submission_id": self._generate_submission_id(),
            "files": files,
            "submitted_at": datetime.utcnow().isoformat()
        }

    def process_bacs_return(
        self,
        instruction_id: str,
        return_code: str
    ) -> dict:
        """
        Handle BACS return (unpaid item)
        """
        instruction = self._get_instruction(instruction_id)

        return_record = {
            "return_id": self._generate_return_id(),
            "original_instruction": instruction_id,
            "return_code": return_code,
            "return_reason": self._get_return_reason(return_code),
            "amount": str(instruction.amount),
            "processed_at": datetime.utcnow().isoformat()
        }

        # Credit funds back
        self._process_return_credit(instruction, return_code)

        return return_record

    def bacs_file(
        self,
        instructions: list[BACSInstruction],
        processing_date: date
    ) -> bytes:
        """
        Generate Standard 18 BACS file format
        """
        lines = []

        # Header record (VOL1)
        lines.append(self._generate_header())

        # User Header Label (UHL1)
        lines.append(self._generate_user_header(processing_date))

        # Contra records
        lines.append(self._generate_contra(instructions))

        # Detail records
        for inst in instructions:
            lines.append(self._generate_detail(inst))

        # End of file record (EOF1)
        lines.append(self._generate_eof(len(instructions)))

        return "\n".join(lines).encode()

    def calculate_processing_date(
        self,
        input_date: date = None
    ) -> date:
        """
        Calculate BACS processing date

        Input by 22:30, processes 2 banking days later
        """
        if input_date is None:
            input_date = date.today()

        processing = input_date
        banking_days = 0

        while banking_days < 2:
            processing += timedelta(days=1)
            if self._is_banking_day(processing):
                banking_days += 1

        return processing


class BACSDirectDebit:
    """
    BACS Direct Debit handling

    For recurring collections
    """

    async def create_ddi(
        self,
        originator_sun: str,
        payer_sort_code: str,
        payer_account: str,
        payer_name: str,
        reference: str
    ) -> dict:
        """
        Create Direct Debit Instruction (DDI)

        Setup mandate via AUDDIS
        """
        ddi = {
            "ddi_reference": self._generate_ddi_reference(),
            "sun": originator_sun,
            "payer_sort_code": payer_sort_code,
            "payer_account": payer_account,
            "payer_name": payer_name,
            "reference": reference,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }

        # Submit via AUDDIS
        await self._submit_auddis(ddi)

        return ddi

    async def collect(
        self,
        ddi_reference: str,
        amount: Decimal,
        collection_date: date
    ) -> BACSInstruction:
        """
        Create Direct Debit collection

        Submit to BACS for processing
        """
        ddi = await self._get_ddi(ddi_reference)

        instruction = BACSInstruction(
            instruction_id=self._generate_instruction_id(),
            instruction_type=BACSType.DIRECT_DEBIT,
            originator_sort_code=self.sort_code,
            originator_account=self.account_number,
            destination_sort_code=ddi["payer_sort_code"],
            destination_account=ddi["payer_account"],
            amount=amount,
            reference=ddi["reference"],
            processing_date=collection_date,
            service_user_number=ddi["sun"]
        )

        return instruction

    async def handle_indemnity_claim(
        self,
        ddi_reference: str,
        claim_amount: Decimal,
        claim_reason: str
    ) -> dict:
        """
        Handle Direct Debit Guarantee indemnity claim

        Payer can claim refund from bank
        """
        return {
            "claim_id": self._generate_claim_id(),
            "ddi_reference": ddi_reference,
            "amount": str(claim_amount),
            "reason": claim_reason,
            "status": "pending",
            "claimed_at": datetime.utcnow().isoformat()
        }
```

## CHAPS Payments

```python
from decimal import Decimal
from datetime import datetime, time, date
from dataclasses import dataclass

@dataclass
class CHAPSPayment:
    """CHAPS high-value payment"""
    payment_id: str
    sender_details: dict
    recipient_details: dict
    amount: Decimal
    currency: str  # Usually GBP
    purpose: str
    status: str
    submitted_at: datetime
    settled_at: Optional[datetime] = None

class CHAPSPayments:
    """
    CHAPS - Clearing House Automated Payment System

    Real-time gross settlement for high-value payments
    """

    # CHAPS operating hours
    OPENING_TIME = time(6, 0)
    CUSTOMER_CUTOFF = time(16, 0)  # 4pm for customer payments
    INTERBANK_CUTOFF = time(18, 0)  # 6pm for interbank

    def submit_chaps(
        self,
        sender_sort_code: str,
        sender_account: str,
        sender_name: str,
        recipient_sort_code: str,
        recipient_account: str,
        recipient_name: str,
        amount: Decimal,
        purpose: str
    ) -> CHAPSPayment:
        """
        Submit CHAPS payment

        Same-day settlement for high-value payments
        """
        # Check operating hours
        if not self._is_chaps_open():
            raise CHAPSClosedError("CHAPS is closed")

        # Check cutoff
        if datetime.now().time() > self.CUSTOMER_CUTOFF:
            raise CutoffPassedError("Customer cutoff time has passed")

        payment = CHAPSPayment(
            payment_id=self._generate_chaps_reference(),
            sender_details={
                "sort_code": sender_sort_code,
                "account": sender_account,
                "name": sender_name
            },
            recipient_details={
                "sort_code": recipient_sort_code,
                "account": recipient_account,
                "name": recipient_name
            },
            amount=amount,
            currency="GBP",
            purpose=purpose,
            status="submitted",
            submitted_at=datetime.utcnow()
        )

        # Submit to CHAPS
        result = self._submit_to_chaps(payment)
        payment.status = result["status"]

        if result["settled"]:
            payment.settled_at = datetime.utcnow()

        return payment

    def chaps_payment(
        self,
        payment_details: dict
    ) -> CHAPSPayment:
        """
        Alternative entry point for CHAPS payment
        """
        return self.submit_chaps(
            sender_sort_code=payment_details["sender"]["sort_code"],
            sender_account=payment_details["sender"]["account"],
            sender_name=payment_details["sender"]["name"],
            recipient_sort_code=payment_details["recipient"]["sort_code"],
            recipient_account=payment_details["recipient"]["account"],
            recipient_name=payment_details["recipient"]["name"],
            amount=Decimal(str(payment_details["amount"])),
            purpose=payment_details.get("purpose", "")
        )

    def high_value_transfer(
        self,
        amount: Decimal,
        sender: dict,
        recipient: dict
    ) -> CHAPSPayment:
        """
        High-value transfer via CHAPS

        Recommended for amounts over £250,000
        """
        return self.submit_chaps(
            sender_sort_code=sender["sort_code"],
            sender_account=sender["account"],
            sender_name=sender["name"],
            recipient_sort_code=recipient["sort_code"],
            recipient_account=recipient["account"],
            recipient_name=recipient["name"],
            amount=amount,
            purpose="High value transfer"
        )

    def _is_chaps_open(self) -> bool:
        """Check if CHAPS is currently operating"""
        now = datetime.now()

        # Check if business day
        if now.weekday() >= 5:
            return False

        # Check if bank holiday
        if self._is_bank_holiday(now.date()):
            return False

        # Check operating hours
        current_time = now.time()
        return self.OPENING_TIME <= current_time <= self.INTERBANK_CUTOFF


class UKPaymentRouting:
    """
    Route payments to appropriate UK scheme
    """

    FPS_LIMIT = Decimal("1000000")
    CHAPS_RECOMMENDED = Decimal("250000")

    def route_payment(
        self,
        amount: Decimal,
        urgency: str,
        recipient_reachable_fps: bool
    ) -> str:
        """
        Determine optimal payment scheme

        Based on amount, urgency, and recipient capability
        """
        # High value - use CHAPS
        if amount >= self.CHAPS_RECOMMENDED:
            return "chaps"

        # Over FPS limit - must use CHAPS
        if amount > self.FPS_LIMIT:
            return "chaps"

        # Real-time needed and recipient supports FPS
        if urgency == "immediate" and recipient_reachable_fps:
            return "fps"

        # Bulk or scheduled - use BACS
        if urgency in ["bulk", "scheduled"]:
            return "bacs"

        # Default to FPS if available
        if recipient_reachable_fps:
            return "fps"

        return "bacs"
```
