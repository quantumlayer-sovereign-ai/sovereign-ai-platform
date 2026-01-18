"""
Rate Limiting for Sovereign AI Platform

Features:
- Token bucket algorithm
- Per-IP and per-user rate limiting
- Configurable limits
- In-memory storage (Redis-compatible interface for future)
"""

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from fastapi import HTTPException, Request

# Configuration
DEFAULT_REQUESTS_PER_MINUTE = int(os.environ.get("RATE_LIMIT_RPM", "100"))
DEFAULT_MAX_CONCURRENT = int(os.environ.get("RATE_LIMIT_CONCURRENT", "10"))
BURST_MULTIPLIER = float(os.environ.get("RATE_LIMIT_BURST", "1.5"))


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    capacity: float
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.time)

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were available, False otherwise
        """
        now = time.time()
        self._refill(now)

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self, now: float):
        """Refill tokens based on time elapsed"""
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    @property
    def wait_time(self) -> float:
        """Time until next token is available"""
        if self.tokens >= 1:
            return 0
        return (1 - self.tokens) / self.refill_rate


@dataclass
class ConcurrencyTracker:
    """Track concurrent requests per user"""
    active: int = 0
    limit: int = DEFAULT_MAX_CONCURRENT
    lock: Lock = field(default_factory=Lock)

    def acquire(self) -> bool:
        """Try to acquire a slot for a new request"""
        with self.lock:
            if self.active < self.limit:
                self.active += 1
                return True
            return False

    def release(self):
        """Release a slot when request completes"""
        with self.lock:
            self.active = max(0, self.active - 1)


class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm

    Features:
    - Per-IP rate limiting
    - Per-user rate limiting (when authenticated)
    - Concurrent request limiting
    - Configurable limits per endpoint
    """

    def __init__(
        self,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        burst_multiplier: float = BURST_MULTIPLIER
    ):
        self.requests_per_minute = requests_per_minute
        self.max_concurrent = max_concurrent
        self.burst_multiplier = burst_multiplier

        # Storage
        self._buckets: dict[str, TokenBucket] = {}
        self._concurrency: dict[str, ConcurrencyTracker] = defaultdict(
            lambda: ConcurrencyTracker(limit=self.max_concurrent)
        )
        self._lock = Lock()

        # Cleanup tracking
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _get_bucket(self, key: str) -> TokenBucket:
        """Get or create a token bucket for a key"""
        with self._lock:
            # Periodic cleanup
            self._maybe_cleanup()

            if key not in self._buckets:
                capacity = self.requests_per_minute * self.burst_multiplier
                refill_rate = self.requests_per_minute / 60.0  # per second

                self._buckets[key] = TokenBucket(
                    capacity=capacity,
                    tokens=capacity,
                    refill_rate=refill_rate
                )

            return self._buckets[key]

    def _maybe_cleanup(self):
        """Clean up old buckets to prevent memory leak"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        # Remove buckets that haven't been used in a while
        stale_keys = [
            key for key, bucket in self._buckets.items()
            if now - bucket.last_refill > 600  # 10 minutes
        ]
        for key in stale_keys:
            del self._buckets[key]

        self._last_cleanup = now

    def check_rate_limit(self, key: str) -> tuple[bool, dict[str, Any]]:
        """
        Check if a request is allowed under rate limits

        Args:
            key: Identifier for rate limiting (IP, user_id, etc.)

        Returns:
            Tuple of (allowed, metadata)
        """
        bucket = self._get_bucket(key)
        allowed = bucket.consume(1)

        metadata = {
            "limit": self.requests_per_minute,
            "remaining": int(bucket.tokens),
            "reset_in": bucket.wait_time if not allowed else 0
        }

        return allowed, metadata

    def acquire_concurrent(self, key: str) -> bool:
        """Acquire a concurrent request slot"""
        return self._concurrency[key].acquire()

    def release_concurrent(self, key: str):
        """Release a concurrent request slot"""
        self._concurrency[key].release()

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "active_buckets": len(self._buckets),
            "active_concurrency_trackers": len(self._concurrency),
            "requests_per_minute": self.requests_per_minute,
            "max_concurrent": self.max_concurrent
        }


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_client_identifier(request: Request, user_id: str | None = None) -> str:
    """
    Get a unique identifier for rate limiting

    Priority:
    1. User ID (if authenticated)
    2. X-Forwarded-For header (if behind proxy)
    3. Client IP
    """
    if user_id:
        return f"user:{user_id}"

    # Check for proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return f"ip:{client_ip}"


class RateLimitDependency:
    """
    FastAPI dependency for rate limiting

    Usage:
        @app.post("/task/execute", dependencies=[Depends(RateLimitDependency())])
        async def execute_task():
            ...

        # Or with custom limits:
        @app.post("/heavy-endpoint", dependencies=[Depends(RateLimitDependency(rpm=10))])
        async def heavy_endpoint():
            ...
    """

    def __init__(
        self,
        rpm: int | None = None,
        max_concurrent: int | None = None,
        check_concurrent: bool = True
    ):
        self.rpm = rpm
        self.max_concurrent = max_concurrent
        self.check_concurrent = check_concurrent

    async def __call__(self, request: Request) -> dict[str, Any]:
        limiter = get_rate_limiter()

        # Get client identifier
        # Check if user is authenticated (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        client_id = get_client_identifier(request, user_id)

        # Check rate limit
        allowed, metadata = limiter.check_rate_limit(client_id)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": metadata["reset_in"],
                    "limit": metadata["limit"]
                },
                headers={
                    "Retry-After": str(int(metadata["reset_in"]) + 1),
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": str(metadata["remaining"])
                }
            )

        # Check concurrent requests
        if self.check_concurrent:
            if not limiter.acquire_concurrent(client_id):
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too many concurrent requests",
                        "max_concurrent": limiter.max_concurrent
                    }
                )

            # Store for cleanup in response
            request.state.rate_limit_client_id = client_id
            request.state.rate_limit_concurrent = True

        # Add rate limit headers info
        return {
            "client_id": client_id,
            "remaining": metadata["remaining"]
        }


async def release_concurrent_slot(request: Request):
    """
    Release concurrent slot after request completes

    Call this in a middleware or background task after response is sent
    """
    if getattr(request.state, "rate_limit_concurrent", False):
        client_id = getattr(request.state, "rate_limit_client_id", None)
        if client_id:
            get_rate_limiter().release_concurrent(client_id)
