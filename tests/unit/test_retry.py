"""
Unit tests for retry module
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.utils.retry import RetryError, retry, with_retry


class TestRetryDecorator:
    """Tests for the @retry decorator"""

    @pytest.mark.asyncio
    async def test_retry_succeeds_first_try(self):
        """Test that successful function doesn't retry"""
        call_count = 0

        @retry(max_attempts=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Test that function succeeds after transient failures"""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01, jitter=False)
        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = await eventually_succeeds()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test that RetryError is raised when all attempts fail"""
        @retry(max_attempts=3, initial_delay=0.01, jitter=False)
        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            await always_fails()

        assert "Failed after 3 attempts" in str(exc_info.value)
        assert exc_info.value.last_exception is not None

    @pytest.mark.asyncio
    async def test_retry_with_specific_exceptions(self):
        """Test that only specified exceptions trigger retry"""
        call_count = 0

        @retry(max_attempts=3, exceptions=(ValueError,), initial_delay=0.01)
        async def raises_different_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Not a ValueError")

        with pytest.raises(TypeError):
            await raises_different_error()

        # Should fail immediately without retrying
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_backoff_increases(self):
        """Test that delays increase with backoff factor"""
        delays = []
        call_count = 0

        @retry(max_attempts=3, initial_delay=1.0, backoff_factor=2.0, jitter=False)
        async def track_delays():
            nonlocal call_count
            call_count += 1
            raise ValueError("Fail")

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(RetryError):
                await track_delays()

            # Check delays: first = 1.0, second = 2.0
            assert len(mock_sleep.call_args_list) == 2
            assert mock_sleep.call_args_list[0][0][0] == pytest.approx(1.0)
            assert mock_sleep.call_args_list[1][0][0] == pytest.approx(2.0)

    @pytest.mark.asyncio
    async def test_retry_max_delay(self):
        """Test that delay is capped at max_delay"""
        @retry(max_attempts=4, initial_delay=10.0, backoff_factor=2.0, max_delay=15.0, jitter=False)
        async def test_func():
            raise ValueError("Fail")

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(RetryError):
                await test_func()

            # All delays should be capped at 15
            for call in mock_sleep.call_args_list:
                assert call[0][0] <= 15.0

    def test_retry_sync_function(self):
        """Test retry decorator works with sync functions"""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01, jitter=False)
        def sync_eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Transient error")
            return "success"

        with patch("time.sleep"):
            result = sync_eventually_succeeds()

        assert result == "success"
        assert call_count == 2


class TestWithRetry:
    """Tests for the with_retry function"""

    @pytest.mark.asyncio
    async def test_with_retry_async_function(self):
        """Test with_retry on async function"""
        call_count = 0

        async def async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Transient")
            return "success"

        result = await with_retry(
            async_func,
            max_attempts=3,
            initial_delay=0.01,
            jitter=False
        )

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_with_retry_sync_function(self):
        """Test with_retry on sync function"""
        call_count = 0

        def sync_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Transient")
            return "success"

        result = await with_retry(
            sync_func,
            max_attempts=3,
            initial_delay=0.01,
            jitter=False
        )

        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_retry_passes_args(self):
        """Test with_retry passes arguments to function"""
        async def func_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = await with_retry(
            func_with_args,
            "hello",
            "world",
            c="test",
            max_attempts=1
        )

        assert result == "hello-world-test"

    @pytest.mark.asyncio
    async def test_with_retry_exhausted(self):
        """Test with_retry raises RetryError when exhausted"""
        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            await with_retry(
                always_fails,
                max_attempts=2,
                initial_delay=0.01,
                jitter=False
            )

        assert "Failed after 2 attempts" in str(exc_info.value)


class TestRetryError:
    """Tests for RetryError exception"""

    def test_retry_error_creation(self):
        """Test creating RetryError"""
        original = ValueError("Original error")
        error = RetryError("Retry failed", last_exception=original)

        assert "Retry failed" in str(error)
        assert error.last_exception is original

    def test_retry_error_without_last_exception(self):
        """Test RetryError without last_exception"""
        error = RetryError("Retry failed")

        assert "Retry failed" in str(error)
        assert error.last_exception is None


class TestRetryJitter:
    """Tests for retry jitter behavior"""

    @pytest.mark.asyncio
    async def test_jitter_varies_delays(self):
        """Test that jitter causes delay variation"""
        delays = []

        @retry(max_attempts=5, initial_delay=1.0, backoff_factor=1.0, jitter=True)
        async def track_delays():
            raise ValueError("Fail")

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(RetryError):
                await track_delays()

            delays = [call[0][0] for call in mock_sleep.call_args_list]

        # With jitter, delays should vary between 0.5 and 1.5 times the base
        for delay in delays:
            assert 0.4 <= delay <= 1.6  # Allow some margin

    @pytest.mark.asyncio
    async def test_no_jitter_consistent_delays(self):
        """Test that no jitter gives consistent delays"""
        @retry(max_attempts=3, initial_delay=1.0, backoff_factor=1.0, jitter=False)
        async def track_delays():
            raise ValueError("Fail")

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(RetryError):
                await track_delays()

            delays = [call[0][0] for call in mock_sleep.call_args_list]

        # Without jitter, all delays should be exactly 1.0
        assert all(d == pytest.approx(1.0) for d in delays)
