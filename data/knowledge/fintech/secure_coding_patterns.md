# Secure Coding Patterns for FinTech Applications

## Overview

This document provides secure coding patterns specifically for financial technology applications. These patterns address common security vulnerabilities while maintaining compliance with PCI-DSS, RBI guidelines, and industry best practices.

## 1. Authentication Patterns

### Multi-Factor Authentication Implementation

```python
from enum import Enum
from datetime import datetime, timedelta
import pyotp
import secrets

class MFAMethod(Enum):
    TOTP = "totp"          # Time-based OTP (Google Authenticator)
    SMS = "sms"            # SMS OTP
    EMAIL = "email"        # Email OTP
    HARDWARE = "hardware"  # Hardware token
    BIOMETRIC = "biometric"  # Fingerprint/Face

class MFAService:
    OTP_VALIDITY = timedelta(minutes=5)
    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = timedelta(minutes=15)

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.attempts = 0
        self.locked_until = None

    def generate_totp_secret(self) -> str:
        """Generate TOTP secret for user"""
        secret = pyotp.random_base32()
        # Store encrypted secret in database
        self._store_mfa_secret(self.user_id, secret)
        return secret

    def verify_totp(self, token: str) -> bool:
        """Verify TOTP token"""
        if self._is_locked():
            raise AccountLocked(f"Account locked until {self.locked_until}")

        secret = self._get_mfa_secret(self.user_id)
        totp = pyotp.TOTP(secret)

        if totp.verify(token, valid_window=1):
            self._reset_attempts()
            self._log_successful_mfa()
            return True

        self._increment_attempts()
        self._log_failed_mfa()
        return False

    def generate_sms_otp(self, phone_number: str) -> str:
        """Generate and send SMS OTP"""
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        expiry = datetime.now() + self.OTP_VALIDITY

        # Store hashed OTP
        self._store_otp_hash(self.user_id, self._hash_otp(otp), expiry)

        # Send via SMS gateway (never log the OTP)
        self._send_sms(phone_number, f"Your OTP is: {otp}")

        return "OTP sent"  # Never return actual OTP

    def verify_sms_otp(self, otp: str) -> bool:
        """Verify SMS OTP"""
        if self._is_locked():
            raise AccountLocked("Too many failed attempts")

        stored_hash, expiry = self._get_otp_hash(self.user_id)

        if datetime.now() > expiry:
            raise OTPExpired("OTP has expired")

        if self._hash_otp(otp) == stored_hash:
            self._invalidate_otp(self.user_id)  # One-time use
            self._reset_attempts()
            return True

        self._increment_attempts()
        return False

    def _is_locked(self) -> bool:
        if self.locked_until and datetime.now() < self.locked_until:
            return True
        return False

    def _increment_attempts(self):
        self.attempts += 1
        if self.attempts >= self.MAX_ATTEMPTS:
            self.locked_until = datetime.now() + self.LOCKOUT_DURATION
            self._log_account_lockout()
```

### Session Management

```python
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import redis

class SecureSessionManager:
    """
    Secure session management for financial applications

    Features:
    - Cryptographically secure session tokens
    - Automatic timeout (PCI-DSS 8.1.8)
    - Concurrent session control
    - Session binding to IP/Device
    """

    SESSION_TIMEOUT = timedelta(minutes=15)
    MAX_CONCURRENT_SESSIONS = 3

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def create_session(self, user_id: str, ip_address: str,
                       device_fingerprint: str) -> str:
        """Create new authenticated session"""

        # Check concurrent session limit
        self._enforce_session_limit(user_id)

        # Generate secure token
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)

        session_data = {
            'user_id': user_id,
            'ip_address': ip_address,
            'device_fingerprint': device_fingerprint,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }

        # Store in Redis with expiry
        self.redis.hset(f"session:{token_hash}", mapping=session_data)
        self.redis.expire(f"session:{token_hash}",
                         int(self.SESSION_TIMEOUT.total_seconds()))

        # Track user's sessions
        self.redis.sadd(f"user_sessions:{user_id}", token_hash)

        self._log_session_created(user_id, ip_address)
        return token

    def validate_session(self, token: str, ip_address: str) -> Optional[str]:
        """Validate session and return user_id"""
        token_hash = self._hash_token(token)
        session_data = self.redis.hgetall(f"session:{token_hash}")

        if not session_data:
            return None

        # Verify IP binding (optional, configurable)
        if session_data.get(b'ip_address', b'').decode() != ip_address:
            self._log_session_ip_mismatch(token_hash, ip_address)
            # Could invalidate or just log based on policy

        # Update last activity (sliding window)
        self.redis.hset(f"session:{token_hash}", 'last_activity',
                       datetime.now().isoformat())
        self.redis.expire(f"session:{token_hash}",
                         int(self.SESSION_TIMEOUT.total_seconds()))

        return session_data.get(b'user_id', b'').decode()

    def invalidate_session(self, token: str):
        """Invalidate a specific session"""
        token_hash = self._hash_token(token)
        session_data = self.redis.hgetall(f"session:{token_hash}")

        if session_data:
            user_id = session_data.get(b'user_id', b'').decode()
            self.redis.delete(f"session:{token_hash}")
            self.redis.srem(f"user_sessions:{user_id}", token_hash)
            self._log_session_invalidated(user_id)

    def invalidate_all_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user (security event)"""
        session_hashes = self.redis.smembers(f"user_sessions:{user_id}")

        for token_hash in session_hashes:
            self.redis.delete(f"session:{token_hash.decode()}")

        self.redis.delete(f"user_sessions:{user_id}")
        self._log_all_sessions_invalidated(user_id)

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _enforce_session_limit(self, user_id: str):
        sessions = self.redis.smembers(f"user_sessions:{user_id}")
        if len(sessions) >= self.MAX_CONCURRENT_SESSIONS:
            # Remove oldest session
            oldest = sorted(sessions)[0]
            self.redis.delete(f"session:{oldest.decode()}")
            self.redis.srem(f"user_sessions:{user_id}", oldest)
```

## 2. Payment Processing Patterns

### Idempotent Payment Handler

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import hashlib
import json

@dataclass
class PaymentRequest:
    merchant_id: str
    customer_id: str
    amount: Decimal
    currency: str
    idempotency_key: str
    payment_method: str
    metadata: dict

class IdempotentPaymentProcessor:
    """
    Idempotent payment processing to prevent duplicate charges

    Critical for financial applications to ensure exactly-once processing
    """

    def __init__(self, db, payment_gateway):
        self.db = db
        self.gateway = payment_gateway

    async def process_payment(self, request: PaymentRequest) -> dict:
        # Check for existing payment with same idempotency key
        existing = await self._get_by_idempotency_key(
            request.merchant_id,
            request.idempotency_key
        )

        if existing:
            # Return cached result (idempotent response)
            return existing['result']

        # Acquire distributed lock to prevent race conditions
        lock = await self._acquire_lock(
            f"payment:{request.merchant_id}:{request.idempotency_key}"
        )

        try:
            # Double-check after acquiring lock
            existing = await self._get_by_idempotency_key(
                request.merchant_id,
                request.idempotency_key
            )
            if existing:
                return existing['result']

            # Create payment record in PENDING state
            payment_id = await self._create_payment_record(request)

            try:
                # Process with payment gateway
                gateway_response = await self.gateway.charge(
                    amount=request.amount,
                    currency=request.currency,
                    payment_method=request.payment_method,
                    metadata={'payment_id': payment_id}
                )

                # Update payment status
                result = {
                    'payment_id': payment_id,
                    'status': 'completed',
                    'gateway_reference': gateway_response['reference'],
                    'amount': str(request.amount),
                    'currency': request.currency
                }

                await self._update_payment(payment_id, 'completed', result)
                return result

            except PaymentGatewayError as e:
                # Handle gateway failure
                result = {
                    'payment_id': payment_id,
                    'status': 'failed',
                    'error': str(e)
                }
                await self._update_payment(payment_id, 'failed', result)
                return result

        finally:
            await self._release_lock(lock)
```

### Secure Amount Handling

```python
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

class MoneyAmount:
    """
    Secure money handling to prevent floating-point errors

    Always use Decimal for financial calculations
    """

    def __init__(self, amount: Union[str, Decimal], currency: str):
        if isinstance(amount, float):
            raise ValueError("Float not allowed for money amounts. Use string or Decimal")

        self.amount = Decimal(str(amount))
        self.currency = currency.upper()
        self.precision = self._get_precision(currency)

    def _get_precision(self, currency: str) -> int:
        """Get decimal precision for currency"""
        CURRENCY_PRECISION = {
            'INR': 2,
            'USD': 2,
            'EUR': 2,
            'JPY': 0,  # Yen has no decimals
            'KWD': 3,  # Kuwaiti Dinar has 3 decimals
        }
        return CURRENCY_PRECISION.get(currency, 2)

    def round(self) -> 'MoneyAmount':
        """Round to currency precision"""
        quantize_exp = Decimal(10) ** -self.precision
        rounded = self.amount.quantize(quantize_exp, rounding=ROUND_HALF_UP)
        return MoneyAmount(rounded, self.currency)

    def __add__(self, other: 'MoneyAmount') -> 'MoneyAmount':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return MoneyAmount(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'MoneyAmount') -> 'MoneyAmount':
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return MoneyAmount(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Decimal) -> 'MoneyAmount':
        return MoneyAmount(self.amount * factor, self.currency)

    def to_smallest_unit(self) -> int:
        """Convert to smallest unit (paisa, cents)"""
        multiplier = 10 ** self.precision
        return int(self.round().amount * multiplier)

    @classmethod
    def from_smallest_unit(cls, amount: int, currency: str) -> 'MoneyAmount':
        """Create from smallest unit"""
        precision = cls(0, currency)._get_precision(currency)
        decimal_amount = Decimal(amount) / (10 ** precision)
        return cls(decimal_amount, currency)

    def __repr__(self):
        return f"{self.currency} {self.round().amount}"

# Usage example
payment_amount = MoneyAmount("1234.56", "INR")
tax = MoneyAmount("123.456", "INR")  # Will be rounded
total = (payment_amount + tax).round()
print(f"Total: {total}")  # INR 1358.02
```

## 3. Data Protection Patterns

### Card Data Tokenization

```python
import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime
import base64

class CardTokenizer:
    """
    Secure card tokenization for PCI-DSS compliance

    - Never stores actual card numbers
    - Uses AES-256-GCM for encryption
    - Generates format-preserving tokens
    """

    def __init__(self, master_key: bytes):
        if len(master_key) != 32:  # 256 bits
            raise ValueError("Master key must be 32 bytes")
        self.aesgcm = AESGCM(master_key)

    def tokenize_card(self, pan: str, expiry: str, customer_id: str) -> str:
        """
        Tokenize card data

        Args:
            pan: Card number (will not be stored)
            expiry: Card expiry (MM/YY)
            customer_id: Customer identifier

        Returns:
            Token that can be used for future transactions
        """
        # Validate card
        self._validate_luhn(pan)

        # Generate unique token
        token = self._generate_token()

        # Create card fingerprint (for duplicate detection)
        fingerprint = self._create_fingerprint(pan)

        # Encrypt card data
        nonce = secrets.token_bytes(12)
        card_data = f"{pan}|{expiry}".encode()
        encrypted = self.aesgcm.encrypt(nonce, card_data, None)

        # Store token mapping (encrypted, never plain)
        self._store_token_mapping(
            token=token,
            encrypted_data=base64.b64encode(nonce + encrypted).decode(),
            fingerprint=fingerprint,
            customer_id=customer_id,
            last_four=pan[-4:],
            card_type=self._detect_card_type(pan)
        )

        return token

    def get_card_info(self, token: str) -> dict:
        """Get non-sensitive card info from token"""
        mapping = self._get_token_mapping(token)
        return {
            'last_four': mapping['last_four'],
            'card_type': mapping['card_type'],
            'tokenized_at': mapping['created_at']
        }

    def process_payment_with_token(self, token: str, amount: Decimal) -> dict:
        """Process payment using stored token"""
        mapping = self._get_token_mapping(token)

        # Decrypt card data for processing
        encrypted = base64.b64decode(mapping['encrypted_data'])
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]

        card_data = self.aesgcm.decrypt(nonce, ciphertext, None).decode()
        pan, expiry = card_data.split('|')

        # Process with payment gateway (card data in memory only)
        result = self._call_payment_gateway(pan, expiry, amount)

        # Clear sensitive data from memory
        del pan, expiry, card_data

        return result

    def _validate_luhn(self, pan: str):
        """Luhn algorithm validation"""
        digits = [int(d) for d in pan]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]

        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))

        if checksum % 10 != 0:
            raise ValueError("Invalid card number")

    def _generate_token(self) -> str:
        """Generate unique, format-preserving token"""
        return f"tok_{secrets.token_urlsafe(24)}"

    def _create_fingerprint(self, pan: str) -> str:
        """Create fingerprint for duplicate detection"""
        return hashlib.sha256(f"salt:{pan}".encode()).hexdigest()

    def _detect_card_type(self, pan: str) -> str:
        if pan.startswith('4'):
            return 'visa'
        elif pan.startswith(('51', '52', '53', '54', '55')):
            return 'mastercard'
        elif pan.startswith(('34', '37')):
            return 'amex'
        elif pan.startswith('6'):
            return 'rupay'
        return 'unknown'
```

### Secure Logging

```python
import re
import structlog
from typing import Any

class SecureLogger:
    """
    Secure logging that masks sensitive data

    PCI-DSS requires that sensitive data never appears in logs
    """

    SENSITIVE_PATTERNS = [
        (r'\b\d{13,19}\b', '[CARD_MASKED]'),              # Card numbers
        (r'\b\d{3,4}\b(?=.*cvv)', '[CVV_MASKED]'),        # CVV
        (r'password["\']?\s*[:=]\s*["\']?[^"\']+', 'password=[MASKED]'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\']+', 'api_key=[MASKED]'),
        (r'\b[A-Z]{5}\d{4}[A-Z]\b', '[PAN_MASKED]'),      # Indian PAN
        (r'\b\d{12}\b', '[AADHAAR_MASKED]'),              # Aadhaar
    ]

    def __init__(self):
        self.logger = structlog.get_logger()

    def _mask_sensitive_data(self, data: Any) -> Any:
        """Recursively mask sensitive data"""
        if isinstance(data, str):
            masked = data
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
            return masked

        elif isinstance(data, dict):
            return {k: self._mask_sensitive_data(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]

        return data

    def info(self, message: str, **kwargs):
        masked_kwargs = self._mask_sensitive_data(kwargs)
        self.logger.info(message, **masked_kwargs)

    def error(self, message: str, **kwargs):
        masked_kwargs = self._mask_sensitive_data(kwargs)
        self.logger.error(message, **masked_kwargs)

    def warning(self, message: str, **kwargs):
        masked_kwargs = self._mask_sensitive_data(kwargs)
        self.logger.warning(message, **masked_kwargs)

# Usage
logger = SecureLogger()
logger.info("Payment processed",
           card_number="4111111111111111",  # Will be masked
           amount=1000,
           customer_id="cust_123")
# Output: Payment processed card_number=[CARD_MASKED] amount=1000 customer_id=cust_123
```

## 4. API Security Patterns

### Rate Limiting

```python
import time
from typing import Tuple
import redis

class RateLimiter:
    """
    Distributed rate limiting using Redis

    Implements sliding window algorithm for accurate limiting
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit

        Args:
            key: Unique identifier (user_id, api_key, ip)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            (allowed, metadata)
        """
        now = time.time()
        window_start = now - window_seconds

        pipe = self.redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(f"ratelimit:{key}", 0, window_start)

        # Count current entries
        pipe.zcard(f"ratelimit:{key}")

        # Add current request
        pipe.zadd(f"ratelimit:{key}", {str(now): now})

        # Set expiry
        pipe.expire(f"ratelimit:{key}", window_seconds)

        results = pipe.execute()
        current_count = results[1]

        metadata = {
            'limit': limit,
            'remaining': max(0, limit - current_count - 1),
            'reset': int(now + window_seconds)
        }

        if current_count >= limit:
            return False, metadata

        return True, metadata

# API endpoint usage
class PaymentAPI:
    RATE_LIMITS = {
        'create_payment': (100, 60),      # 100 per minute
        'get_transaction': (1000, 60),    # 1000 per minute
        'refund': (10, 60),               # 10 per minute
    }

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter

    def create_payment(self, merchant_id: str, request: dict):
        limit, window = self.RATE_LIMITS['create_payment']
        allowed, meta = self.rate_limiter.check_rate_limit(
            f"create_payment:{merchant_id}",
            limit,
            window
        )

        if not allowed:
            raise RateLimitExceeded(
                f"Rate limit exceeded. Retry after {meta['reset']}"
            )

        # Process payment...
```

### Request Signing

```python
import hmac
import hashlib
import time
from typing import Optional

class RequestSigner:
    """
    HMAC-based request signing for API security

    Prevents tampering and replay attacks
    """

    TIMESTAMP_TOLERANCE = 300  # 5 minutes

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()

    def sign_request(
        self,
        method: str,
        path: str,
        body: str,
        timestamp: Optional[int] = None
    ) -> dict:
        """Generate signature headers for request"""
        timestamp = timestamp or int(time.time())

        payload = f"{method.upper()}\n{path}\n{timestamp}\n{body}"
        signature = hmac.new(
            self.secret_key,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            'X-Timestamp': str(timestamp),
            'X-Signature': signature
        }

    def verify_request(
        self,
        method: str,
        path: str,
        body: str,
        timestamp: str,
        signature: str
    ) -> bool:
        """Verify request signature"""
        # Check timestamp freshness (prevent replay)
        request_time = int(timestamp)
        current_time = int(time.time())

        if abs(current_time - request_time) > self.TIMESTAMP_TOLERANCE:
            raise SignatureExpired("Request timestamp too old")

        # Verify signature
        payload = f"{method.upper()}\n{path}\n{timestamp}\n{body}"
        expected = hmac.new(
            self.secret_key,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise InvalidSignature("Request signature mismatch")

        return True
```

## 5. Database Security Patterns

### Encrypted Fields

```python
from sqlalchemy import TypeDecorator, String
from cryptography.fernet import Fernet
import base64

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type for encrypted string fields

    Use for PII and sensitive data at rest
    """

    impl = String
    cache_ok = True

    def __init__(self, key: bytes):
        super().__init__()
        self.fernet = Fernet(key)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        encrypted = self.fernet.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        encrypted = base64.b64decode(value.encode())
        return self.fernet.decrypt(encrypted).decode()

# Usage in model
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
ENCRYPTION_KEY = Fernet.generate_key()

class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True)
    email = Column(String(255))  # Not encrypted
    phone = Column(EncryptedString(ENCRYPTION_KEY))  # Encrypted
    pan_number = Column(EncryptedString(ENCRYPTION_KEY))  # Encrypted
```

### Audit Trail

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, event
from sqlalchemy.orm import Session

class AuditLog(Base):
    """Immutable audit log for compliance"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(255))

def create_audit_listener(model_class, resource_type: str):
    """Create SQLAlchemy event listener for automatic auditing"""

    @event.listens_for(model_class, 'after_update')
    def audit_update(mapper, connection, target):
        session = Session.object_session(target)
        if session:
            # Get changed attributes
            changes = {}
            for attr in target.__mapper__.columns:
                hist = get_history(target, attr.key)
                if hist.has_changes():
                    changes[attr.key] = {
                        'old': hist.deleted[0] if hist.deleted else None,
                        'new': hist.added[0] if hist.added else None
                    }

            if changes:
                audit = AuditLog(
                    user_id=get_current_user_id(),
                    action='update',
                    resource_type=resource_type,
                    resource_id=str(target.id),
                    old_values={k: v['old'] for k, v in changes.items()},
                    new_values={k: v['new'] for k, v in changes.items()},
                    ip_address=get_client_ip()
                )
                session.add(audit)

# Apply to models
create_audit_listener(Transaction, 'transaction')
create_audit_listener(Customer, 'customer')
```

This document provides foundational patterns. Each pattern should be adapted to specific use cases and compliance requirements.
