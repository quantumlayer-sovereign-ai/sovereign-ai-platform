"""
FINTECH PAYMENT SERVICE TEMPLATE
================================
Production-ready payment processing service with:
- PCI-DSS compliance patterns
- Proper decimal handling for money
- Idempotency keys
- Audit logging
- Transaction management
"""

# ============================================================================
# FILE: app/models/payment_schemas.py
# ============================================================================
"""Payment-related Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Supported payment methods."""
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"


class PaymentRequest(BaseModel):
    """Payment creation request."""

    amount: Decimal = Field(
        ...,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        description="Payment amount in INR",
    )
    currency: str = Field(default="INR", pattern="^[A-Z]{3}$")
    payment_method: PaymentMethod
    customer_id: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    idempotency_key: str = Field(
        ...,
        min_length=16,
        max_length=64,
        description="Unique key for idempotent requests",
    )
    metadata: Optional[dict] = None

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount is Decimal for precision."""
        if isinstance(v, float):
            # Convert float to string first to avoid precision issues
            return Decimal(str(v))
        return Decimal(v) if not isinstance(v, Decimal) else v


class PaymentResponse(BaseModel):
    """Payment response schema."""

    payment_id: UUID
    status: PaymentStatus
    amount: Decimal
    currency: str
    customer_id: str
    created_at: datetime
    updated_at: datetime
    idempotency_key: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefundRequest(BaseModel):
    """Refund request schema."""

    payment_id: UUID
    amount: Optional[Decimal] = Field(
        None,
        gt=Decimal("0"),
        description="Partial refund amount. If null, full refund.",
    )
    reason: str = Field(..., min_length=1, max_length=255)
    idempotency_key: str


# ============================================================================
# FILE: app/models/payment_models.py
# ============================================================================
"""SQLAlchemy models for payments."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Payment(Base):
    """Payment database model."""

    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
    )
    payment_method: Mapped[str] = mapped_column(String(20))
    customer_id: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PaymentAuditLog(Base):
    """Audit log for payment operations."""

    __tablename__ = "payment_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), index=True)
    action: Mapped[str] = mapped_column(String(50))
    old_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20))
    actor: Mapped[str] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ============================================================================
# FILE: app/services/payment_service.py
# ============================================================================
"""Payment business logic service."""
import json
import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_models import Payment, PaymentAuditLog
from app.models.payment_schemas import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    RefundRequest,
)

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling payment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment(
        self,
        request: PaymentRequest,
        actor: str = "system",
        ip_address: Optional[str] = None,
    ) -> PaymentResponse:
        """
        Create a new payment with idempotency check.

        Args:
            request: Payment request data
            actor: User/system creating the payment
            ip_address: Client IP for audit logging

        Returns:
            PaymentResponse with payment details
        """
        # Check idempotency - return existing if found
        existing = await self._get_by_idempotency_key(request.idempotency_key)
        if existing:
            logger.info(
                "Idempotent request detected",
                extra={"idempotency_key": request.idempotency_key},
            )
            return self._to_response(existing)

        # Create new payment
        payment = Payment(
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method.value,
            customer_id=request.customer_id,
            description=request.description,
            idempotency_key=request.idempotency_key,
            metadata_json=json.dumps(request.metadata) if request.metadata else None,
            status=PaymentStatus.PENDING.value,
        )

        self.session.add(payment)
        await self.session.flush()

        # Create audit log
        await self._create_audit_log(
            payment_id=payment.id,
            action="CREATE",
            old_status=None,
            new_status=PaymentStatus.PENDING.value,
            actor=actor,
            ip_address=ip_address,
        )

        await self.session.refresh(payment)

        logger.info(
            "Payment created",
            extra={
                "payment_id": str(payment.id),
                "amount": str(payment.amount),
                "customer_id": payment.customer_id,
            },
        )

        return self._to_response(payment)

    async def get_payment(self, payment_id: UUID) -> Optional[PaymentResponse]:
        """Get payment by ID."""
        payment = await self._get_by_id(payment_id)
        return self._to_response(payment) if payment else None

    async def process_payment(
        self,
        payment_id: UUID,
        actor: str = "system",
        ip_address: Optional[str] = None,
    ) -> PaymentResponse:
        """
        Process a pending payment.

        In production, this would integrate with payment gateway.
        """
        payment = await self._get_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        if payment.status != PaymentStatus.PENDING.value:
            raise ValueError(f"Payment is not pending: {payment.status}")

        old_status = payment.status

        try:
            # Simulate payment processing
            # In production: call payment gateway API
            payment.status = PaymentStatus.COMPLETED.value

        except Exception as e:
            payment.status = PaymentStatus.FAILED.value
            payment.error_message = str(e)
            logger.error(
                "Payment processing failed",
                extra={"payment_id": str(payment_id), "error": str(e)},
            )

        # Create audit log
        await self._create_audit_log(
            payment_id=payment.id,
            action="PROCESS",
            old_status=old_status,
            new_status=payment.status,
            actor=actor,
            ip_address=ip_address,
        )

        await self.session.flush()
        await self.session.refresh(payment)

        return self._to_response(payment)

    async def refund_payment(
        self,
        request: RefundRequest,
        actor: str = "system",
        ip_address: Optional[str] = None,
    ) -> PaymentResponse:
        """Process a refund for a completed payment."""
        payment = await self._get_by_id(request.payment_id)
        if not payment:
            raise ValueError(f"Payment {request.payment_id} not found")

        if payment.status != PaymentStatus.COMPLETED.value:
            raise ValueError("Only completed payments can be refunded")

        refund_amount = request.amount or payment.amount
        if refund_amount > payment.amount:
            raise ValueError("Refund amount exceeds payment amount")

        old_status = payment.status
        payment.status = PaymentStatus.REFUNDED.value

        # Create audit log with refund details
        await self._create_audit_log(
            payment_id=payment.id,
            action="REFUND",
            old_status=old_status,
            new_status=payment.status,
            actor=actor,
            ip_address=ip_address,
            details=json.dumps({
                "refund_amount": str(refund_amount),
                "reason": request.reason,
            }),
        )

        await self.session.flush()
        await self.session.refresh(payment)

        logger.info(
            "Payment refunded",
            extra={
                "payment_id": str(payment.id),
                "refund_amount": str(refund_amount),
            },
        )

        return self._to_response(payment)

    async def _get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID."""
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def _get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        """Get payment by idempotency key."""
        result = await self.session.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def _create_audit_log(
        self,
        payment_id: UUID,
        action: str,
        old_status: Optional[str],
        new_status: str,
        actor: str,
        ip_address: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        """Create an audit log entry."""
        audit_log = PaymentAuditLog(
            payment_id=payment_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            actor=actor,
            ip_address=ip_address,
            details=details,
        )
        self.session.add(audit_log)

    @staticmethod
    def _to_response(payment: Payment) -> PaymentResponse:
        """Convert Payment model to response schema."""
        return PaymentResponse(
            payment_id=payment.id,
            status=PaymentStatus(payment.status),
            amount=payment.amount,
            currency=payment.currency,
            customer_id=payment.customer_id,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            idempotency_key=payment.idempotency_key,
            error_message=payment.error_message,
        )


# ============================================================================
# FILE: app/routers/payments.py
# ============================================================================
"""Payment API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.payment_schemas import (
    PaymentRequest,
    PaymentResponse,
    RefundRequest,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


def get_payment_service(
    session: AsyncSession = Depends(get_db),
) -> PaymentService:
    """Dependency for PaymentService."""
    return PaymentService(session)


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    request: PaymentRequest,
    http_request: Request,
    x_actor: Optional[str] = Header(default="api-user"),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """
    Create a new payment.

    The idempotency_key ensures that duplicate requests return
    the same response without creating duplicate payments.
    """
    try:
        return await service.create_payment(
            request=request,
            actor=x_actor,
            ip_address=http_request.client.host if http_request.client else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """Get a payment by ID."""
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    return payment


@router.post("/{payment_id}/process", response_model=PaymentResponse)
async def process_payment(
    payment_id: UUID,
    http_request: Request,
    x_actor: Optional[str] = Header(default="api-user"),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """Process a pending payment."""
    try:
        return await service.process_payment(
            payment_id=payment_id,
            actor=x_actor,
            ip_address=http_request.client.host if http_request.client else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/refund", response_model=PaymentResponse)
async def refund_payment(
    request: RefundRequest,
    http_request: Request,
    x_actor: Optional[str] = Header(default="api-user"),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """Refund a completed payment."""
    try:
        return await service.refund_payment(
            request=request,
            actor=x_actor,
            ip_address=http_request.client.host if http_request.client else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
