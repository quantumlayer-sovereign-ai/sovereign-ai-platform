"""
Unit tests for rate limiting module
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.ratelimit import (
    ConcurrencyTracker,
    RateLimitDependency,
    RateLimiter,
    TokenBucket,
    get_client_identifier,
    get_rate_limiter,
)


class TestTokenBucket:
    """Tests for TokenBucket rate limiting algorithm"""

    def test_bucket_creation(self):
        """Test creating a token bucket"""
        bucket = TokenBucket(
            capacity=10.0,
            tokens=10.0,
            refill_rate=1.0
        )

        assert bucket.capacity == 10.0
        assert bucket.tokens == 10.0
        assert bucket.refill_rate == 1.0

    def test_consume_tokens_success(self):
        """Test consuming tokens when available"""
        bucket = TokenBucket(capacity=10.0, tokens=10.0, refill_rate=0.0)  # No refill

        assert bucket.consume(1)
        assert bucket.tokens == pytest.approx(9.0, rel=0.01)

        assert bucket.consume(5)
        assert bucket.tokens == pytest.approx(4.0, rel=0.01)

    def test_consume_tokens_fail_insufficient(self):
        """Test consuming fails when insufficient tokens"""
        bucket = TokenBucket(capacity=10.0, tokens=2.0, refill_rate=0.0)  # No refill

        assert not bucket.consume(5)
        assert bucket.tokens == pytest.approx(2.0, rel=0.01)  # Tokens unchanged

    def test_token_refill(self):
        """Test tokens refill over time"""
        bucket = TokenBucket(capacity=10.0, tokens=5.0, refill_rate=10.0)  # 10 tokens/sec
        original_time = bucket.last_refill

        # Simulate time passing
        bucket.last_refill = original_time - 0.5  # 0.5 seconds ago
        bucket._refill(time.time())

        # Should have refilled ~5 tokens (10 tokens/sec * 0.5 sec)
        assert bucket.tokens >= 9.0  # Allow for timing variations

    def test_token_refill_capped_at_capacity(self):
        """Test that refill doesn't exceed capacity"""
        bucket = TokenBucket(capacity=10.0, tokens=9.0, refill_rate=100.0)
        bucket.last_refill = time.time() - 1.0  # 1 second ago

        bucket._refill(time.time())

        assert bucket.tokens == 10.0  # Capped at capacity

    def test_wait_time_when_empty(self):
        """Test wait_time calculation"""
        bucket = TokenBucket(capacity=10.0, tokens=0.0, refill_rate=2.0)  # 2 tokens/sec

        # With 0 tokens and 2 tokens/sec, should need 0.5 seconds for 1 token
        assert bucket.wait_time == pytest.approx(0.5, rel=0.01)

    def test_wait_time_when_available(self):
        """Test wait_time is 0 when tokens available"""
        bucket = TokenBucket(capacity=10.0, tokens=5.0, refill_rate=1.0)

        assert bucket.wait_time == 0


class TestConcurrencyTracker:
    """Tests for concurrent request tracking"""

    def test_acquire_success(self):
        """Test acquiring a slot when under limit"""
        tracker = ConcurrencyTracker(active=0, limit=5)

        assert tracker.acquire()
        assert tracker.active == 1

    def test_acquire_fail_at_limit(self):
        """Test acquiring fails when at limit"""
        tracker = ConcurrencyTracker(active=5, limit=5)

        assert not tracker.acquire()
        assert tracker.active == 5  # Unchanged

    def test_release(self):
        """Test releasing a slot"""
        tracker = ConcurrencyTracker(active=3, limit=5)

        tracker.release()
        assert tracker.active == 2

    def test_release_doesnt_go_negative(self):
        """Test release doesn't go below 0"""
        tracker = ConcurrencyTracker(active=0, limit=5)

        tracker.release()
        assert tracker.active == 0


class TestRateLimiter:
    """Tests for the main RateLimiter class"""

    def test_rate_limiter_creation(self):
        """Test creating a rate limiter"""
        limiter = RateLimiter(
            requests_per_minute=60,
            max_concurrent=10,
            burst_multiplier=1.5
        )

        assert limiter.requests_per_minute == 60
        assert limiter.max_concurrent == 10
        assert limiter.burst_multiplier == 1.5

    def test_check_rate_limit_allowed(self):
        """Test rate limit check when allowed"""
        limiter = RateLimiter(requests_per_minute=100)

        allowed, metadata = limiter.check_rate_limit("test-key")

        assert allowed
        assert metadata["limit"] == 100
        assert metadata["remaining"] > 0

    def test_check_rate_limit_exhausted(self):
        """Test rate limit check when exhausted"""
        limiter = RateLimiter(requests_per_minute=2, burst_multiplier=1.0)

        # Exhaust the bucket
        limiter.check_rate_limit("test-key")
        limiter.check_rate_limit("test-key")

        allowed, metadata = limiter.check_rate_limit("test-key")

        assert not allowed
        assert metadata["reset_in"] > 0

    def test_concurrent_acquire_release(self):
        """Test concurrent slot management"""
        limiter = RateLimiter(max_concurrent=2)

        assert limiter.acquire_concurrent("user1")
        assert limiter.acquire_concurrent("user1")
        assert not limiter.acquire_concurrent("user1")  # At limit

        limiter.release_concurrent("user1")
        assert limiter.acquire_concurrent("user1")  # Can acquire again

    def test_get_stats(self):
        """Test getting rate limiter statistics"""
        limiter = RateLimiter()
        limiter.check_rate_limit("user1")
        limiter.check_rate_limit("user2")

        stats = limiter.get_stats()

        assert stats["active_buckets"] == 2
        assert "requests_per_minute" in stats
        assert "max_concurrent" in stats

    def test_cleanup_old_buckets(self):
        """Test that old buckets are cleaned up"""
        limiter = RateLimiter()
        limiter._cleanup_interval = 0  # Force cleanup every time

        # Create a bucket
        limiter.check_rate_limit("old-key")

        # Manually age the bucket
        limiter._buckets["old-key"].last_refill = time.time() - 700  # 11+ minutes ago
        limiter._last_cleanup = time.time() - 1  # Force cleanup

        # Trigger cleanup through another check
        limiter.check_rate_limit("new-key")

        assert "old-key" not in limiter._buckets


class TestGetClientIdentifier:
    """Tests for client identifier extraction"""

    def test_get_client_identifier_with_user_id(self):
        """Test identifier uses user_id when provided"""
        request = MagicMock()

        identifier = get_client_identifier(request, user_id="user123")

        assert identifier == "user:user123"

    def test_get_client_identifier_from_x_forwarded_for(self):
        """Test identifier from X-Forwarded-For header"""
        request = MagicMock()
        request.headers.get.return_value = "1.2.3.4, 5.6.7.8"

        identifier = get_client_identifier(request, user_id=None)

        assert identifier == "ip:1.2.3.4"

    def test_get_client_identifier_from_client_ip(self):
        """Test identifier from client IP"""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "192.168.1.1"

        identifier = get_client_identifier(request, user_id=None)

        assert identifier == "ip:192.168.1.1"


class TestRateLimitDependency:
    """Tests for the FastAPI rate limit dependency"""

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_allowed(self):
        """Test dependency allows request when under limit"""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "127.0.0.1"
        request.state = MagicMock()

        dependency = RateLimitDependency()

        with patch("api.ratelimit.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value.check_rate_limit.return_value = (True, {"limit": 100, "remaining": 99})
            mock_limiter.return_value.acquire_concurrent.return_value = True

            result = await dependency(request)

            assert "client_id" in result
            assert "remaining" in result

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_rate_exceeded(self):
        """Test dependency raises 429 when rate exceeded"""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "127.0.0.1"
        request.state = MagicMock()

        dependency = RateLimitDependency()

        with patch("api.ratelimit.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value.check_rate_limit.return_value = (False, {"limit": 100, "remaining": 0, "reset_in": 5.0})

            with pytest.raises(HTTPException) as exc_info:
                await dependency(request)

            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_concurrent_exceeded(self):
        """Test dependency raises 429 when concurrent limit exceeded"""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "127.0.0.1"
        request.state = MagicMock()

        dependency = RateLimitDependency(check_concurrent=True)

        with patch("api.ratelimit.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value.check_rate_limit.return_value = (True, {"limit": 100, "remaining": 99})
            mock_limiter.return_value.acquire_concurrent.return_value = False
            mock_limiter.return_value.max_concurrent = 10

            with pytest.raises(HTTPException) as exc_info:
                await dependency(request)

            assert exc_info.value.status_code == 429
            assert "concurrent" in str(exc_info.value.detail).lower()


class TestGlobalRateLimiter:
    """Tests for global rate limiter singleton"""

    def test_get_rate_limiter_returns_same_instance(self):
        """Test that get_rate_limiter returns singleton"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2
