"""
FINTECH WALLET SERVICE TEMPLATE
===============================
Production-ready wallet service with:
- Thread-safe balance operations
- Transaction history
- Overdraft protection
- Audit logging
"""

# ============================================================================
# FILE: app/models/wallet_schemas.py
# ============================================================================
"""Wallet-related Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionType(str, Enum):
    """Types of wallet transactions."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    REFUND = "refund"
    FEE = "fee"


class WalletResponse(BaseModel):
    """Wallet information response."""

    wallet_id: UUID
    user_id: str
    balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepositRequest(BaseModel):
    """Deposit funds request."""

    amount: Decimal = Field(
        ...,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        description="Amount to deposit",
    )
    reference: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    idempotency_key: str = Field(..., min_length=16, max_length=64)

    @field_validator("amount", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        if isinstance(v, float):
            return Decimal(str(v))
        return Decimal(v) if not isinstance(v, Decimal) else v


class WithdrawRequest(BaseModel):
    """Withdraw funds request."""

    amount: Decimal = Field(
        ...,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        description="Amount to withdraw",
    )
    reference: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    idempotency_key: str = Field(..., min_length=16, max_length=64)

    @field_validator("amount", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        if isinstance(v, float):
            return Decimal(str(v))
        return Decimal(v) if not isinstance(v, Decimal) else v


class TransferRequest(BaseModel):
    """Transfer funds between wallets."""

    to_wallet_id: UUID
    amount: Decimal = Field(
        ...,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    description: Optional[str] = Field(None, max_length=255)
    idempotency_key: str = Field(..., min_length=16, max_length=64)


class TransactionResponse(BaseModel):
    """Transaction record response."""

    transaction_id: UUID
    wallet_id: UUID
    transaction_type: TransactionType
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reference: str
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# FILE: app/models/wallet_models.py
# ============================================================================
"""SQLAlchemy models for wallet."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Numeric, String, Text, Boolean, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Wallet(Base):
    """Wallet database model."""

    __tablename__ = "wallets"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        default=Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

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

    # Relationships
    transactions: Mapped[list["WalletTransaction"]] = relationship(
        back_populates="wallet",
        lazy="dynamic",
    )


class WalletTransaction(Base):
    """Wallet transaction record."""

    __tablename__ = "wallet_transactions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    wallet_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wallets.id"),
        index=True,
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    balance_before: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    reference: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")


# ============================================================================
# FILE: app/services/wallet_service.py
# ============================================================================
"""Wallet business logic service."""
import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet_models import Wallet, WalletTransaction
from app.models.wallet_schemas import (
    DepositRequest,
    TransactionResponse,
    TransactionType,
    TransferRequest,
    WalletResponse,
    WithdrawRequest,
)

logger = logging.getLogger(__name__)


class InsufficientFundsError(Exception):
    """Raised when wallet has insufficient funds."""
    pass


class WalletNotFoundError(Exception):
    """Raised when wallet is not found."""
    pass


class WalletInactiveError(Exception):
    """Raised when wallet is inactive."""
    pass


class WalletService:
    """Service for wallet operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_wallet(self, user_id: str, currency: str = "INR") -> WalletResponse:
        """Create a new wallet for a user."""
        # Check if wallet already exists
        existing = await self._get_wallet_by_user_id(user_id)
        if existing:
            raise ValueError(f"Wallet already exists for user {user_id}")

        wallet = Wallet(
            user_id=user_id,
            currency=currency,
            balance=Decimal("0.00"),
        )
        self.session.add(wallet)
        await self.session.flush()
        await self.session.refresh(wallet)

        logger.info("Wallet created", extra={"user_id": user_id, "wallet_id": str(wallet.id)})
        return self._to_wallet_response(wallet)

    async def get_wallet(self, wallet_id: UUID) -> Optional[WalletResponse]:
        """Get wallet by ID."""
        wallet = await self._get_wallet_by_id(wallet_id)
        return self._to_wallet_response(wallet) if wallet else None

    async def get_wallet_by_user(self, user_id: str) -> Optional[WalletResponse]:
        """Get wallet by user ID."""
        wallet = await self._get_wallet_by_user_id(user_id)
        return self._to_wallet_response(wallet) if wallet else None

    async def deposit(
        self,
        wallet_id: UUID,
        request: DepositRequest,
    ) -> TransactionResponse:
        """
        Deposit funds into wallet.

        Uses row-level locking to ensure thread safety.
        """
        # Check idempotency
        existing_tx = await self._get_transaction_by_idempotency_key(request.idempotency_key)
        if existing_tx:
            logger.info("Idempotent deposit request", extra={"key": request.idempotency_key})
            return self._to_transaction_response(existing_tx)

        # Get wallet with lock
        wallet = await self._get_wallet_for_update(wallet_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")
        if not wallet.is_active:
            raise WalletInactiveError(f"Wallet {wallet_id} is inactive")

        balance_before = wallet.balance
        balance_after = balance_before + request.amount

        # Update balance
        wallet.balance = balance_after

        # Create transaction record
        transaction = WalletTransaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.DEPOSIT.value,
            amount=request.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            reference=request.reference,
            idempotency_key=request.idempotency_key,
            description=request.description,
        )
        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)

        logger.info(
            "Deposit completed",
            extra={
                "wallet_id": str(wallet_id),
                "amount": str(request.amount),
                "balance": str(balance_after),
            },
        )

        return self._to_transaction_response(transaction)

    async def withdraw(
        self,
        wallet_id: UUID,
        request: WithdrawRequest,
    ) -> TransactionResponse:
        """
        Withdraw funds from wallet.

        Checks for sufficient balance before withdrawal.
        """
        # Check idempotency
        existing_tx = await self._get_transaction_by_idempotency_key(request.idempotency_key)
        if existing_tx:
            return self._to_transaction_response(existing_tx)

        # Get wallet with lock
        wallet = await self._get_wallet_for_update(wallet_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")
        if not wallet.is_active:
            raise WalletInactiveError(f"Wallet {wallet_id} is inactive")

        balance_before = wallet.balance
        if balance_before < request.amount:
            raise InsufficientFundsError(
                f"Insufficient funds. Available: {balance_before}, Requested: {request.amount}"
            )

        balance_after = balance_before - request.amount

        # Update balance
        wallet.balance = balance_after

        # Create transaction record
        transaction = WalletTransaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.WITHDRAWAL.value,
            amount=request.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            reference=request.reference,
            idempotency_key=request.idempotency_key,
            description=request.description,
        )
        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)

        logger.info(
            "Withdrawal completed",
            extra={
                "wallet_id": str(wallet_id),
                "amount": str(request.amount),
                "balance": str(balance_after),
            },
        )

        return self._to_transaction_response(transaction)

    async def get_transactions(
        self,
        wallet_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TransactionResponse]:
        """Get transaction history for a wallet."""
        result = await self.session.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet_id)
            .order_by(WalletTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        transactions = result.scalars().all()
        return [self._to_transaction_response(tx) for tx in transactions]

    async def _get_wallet_by_id(self, wallet_id: UUID) -> Optional[Wallet]:
        """Get wallet by ID."""
        result = await self.session.execute(
            select(Wallet).where(Wallet.id == wallet_id)
        )
        return result.scalar_one_or_none()

    async def _get_wallet_by_user_id(self, user_id: str) -> Optional[Wallet]:
        """Get wallet by user ID."""
        result = await self.session.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_wallet_for_update(self, wallet_id: UUID) -> Optional[Wallet]:
        """Get wallet with row-level lock for update."""
        result = await self.session.execute(
            select(Wallet)
            .where(Wallet.id == wallet_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def _get_transaction_by_idempotency_key(
        self, key: str
    ) -> Optional[WalletTransaction]:
        """Get transaction by idempotency key."""
        result = await self.session.execute(
            select(WalletTransaction).where(WalletTransaction.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_wallet_response(wallet: Wallet) -> WalletResponse:
        """Convert Wallet model to response schema."""
        return WalletResponse(
            wallet_id=wallet.id,
            user_id=wallet.user_id,
            balance=wallet.balance,
            currency=wallet.currency,
            is_active=wallet.is_active,
            created_at=wallet.created_at,
            updated_at=wallet.updated_at,
        )

    @staticmethod
    def _to_transaction_response(tx: WalletTransaction) -> TransactionResponse:
        """Convert WalletTransaction model to response schema."""
        return TransactionResponse(
            transaction_id=tx.id,
            wallet_id=tx.wallet_id,
            transaction_type=TransactionType(tx.transaction_type),
            amount=tx.amount,
            balance_before=tx.balance_before,
            balance_after=tx.balance_after,
            reference=tx.reference,
            description=tx.description,
            created_at=tx.created_at,
        )


# ============================================================================
# FILE: app/routers/wallets.py
# ============================================================================
"""Wallet API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.wallet_schemas import (
    DepositRequest,
    TransactionResponse,
    WalletResponse,
    WithdrawRequest,
)
from app.services.wallet_service import (
    InsufficientFundsError,
    WalletInactiveError,
    WalletNotFoundError,
    WalletService,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


def get_wallet_service(session: AsyncSession = Depends(get_db)) -> WalletService:
    """Dependency for WalletService."""
    return WalletService(session)


@router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    user_id: str,
    currency: str = "INR",
    service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    """Create a new wallet for a user."""
    try:
        return await service.create_wallet(user_id=user_id, currency=currency)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: UUID,
    service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    """Get wallet by ID."""
    wallet = await service.get_wallet(wallet_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet {wallet_id} not found",
        )
    return wallet


@router.post("/{wallet_id}/deposit", response_model=TransactionResponse)
async def deposit(
    wallet_id: UUID,
    request: DepositRequest,
    service: WalletService = Depends(get_wallet_service),
) -> TransactionResponse:
    """Deposit funds into wallet."""
    try:
        return await service.deposit(wallet_id=wallet_id, request=request)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except WalletInactiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{wallet_id}/withdraw", response_model=TransactionResponse)
async def withdraw(
    wallet_id: UUID,
    request: WithdrawRequest,
    service: WalletService = Depends(get_wallet_service),
) -> TransactionResponse:
    """Withdraw funds from wallet."""
    try:
        return await service.withdraw(wallet_id=wallet_id, request=request)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except WalletInactiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{wallet_id}/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    wallet_id: UUID,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    service: WalletService = Depends(get_wallet_service),
) -> list[TransactionResponse]:
    """Get transaction history for a wallet."""
    return await service.get_transactions(
        wallet_id=wallet_id,
        limit=limit,
        offset=offset,
    )
