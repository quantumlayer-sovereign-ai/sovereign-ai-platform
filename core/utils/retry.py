"""
Retry Utilities for Sovereign AI Platform

Features:
- Exponential backoff retry decorator
- Configurable max attempts and backoff factor
- Support for async functions
- Customizable exception handling
"""

import asyncio
import functools
import random
from collections.abc import Callable
from typing import Any, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted"""

    def __init__(self, message: str, last_exception: Exception | None = None):
        super().__init__(message)
        self.last_exception = last_exception


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    jitter: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying functions with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts (default 3)
        backoff_factor: Multiplier for delay between retries (default 2.0)
        initial_delay: Initial delay in seconds (default 1.0)
        max_delay: Maximum delay between retries (default 60.0)
        exceptions: Tuple of exceptions to catch and retry on
        jitter: Add random jitter to prevent thundering herd (default True)

    Returns:
        Decorated function with retry logic

    Example:
        @retry(max_attempts=3, backoff_factor=2.0)
        async def call_api():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            delay = initial_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(e)
                        )
                        raise RetryError(
                            f"Failed after {max_attempts} attempts: {e}",
                            last_exception=e
                        ) from e

                    # Calculate next delay with exponential backoff
                    actual_delay = min(delay, max_delay)
                    if jitter:
                        actual_delay = actual_delay * (0.5 + random.random())

                    logger.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=actual_delay,
                        error=str(e)
                    )

                    await asyncio.sleep(actual_delay)
                    delay *= backoff_factor

            # This should never be reached, but just in case
            raise RetryError(
                f"Failed after {max_attempts} attempts",
                last_exception=last_exception
            )

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            delay = initial_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(e)
                        )
                        raise RetryError(
                            f"Failed after {max_attempts} attempts: {e}",
                            last_exception=e
                        ) from e

                    # Calculate next delay with exponential backoff
                    actual_delay = min(delay, max_delay)
                    if jitter:
                        actual_delay = actual_delay * (0.5 + random.random())

                    logger.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=actual_delay,
                        error=str(e)
                    )

                    import time
                    time.sleep(actual_delay)
                    delay *= backoff_factor

            # This should never be reached, but just in case
            raise RetryError(
                f"Failed after {max_attempts} attempts",
                last_exception=last_exception
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


async def with_retry(
    func: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    jitter: bool = True,
    **kwargs: Any
) -> T:
    """
    Execute a function with retry logic (non-decorator version)

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry on
        jitter: Add random jitter to prevent thundering herd
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function

    Example:
        result = await with_retry(
            call_api,
            url="https://api.example.com",
            max_attempts=5,
            backoff_factor=2.0
        )
    """
    last_exception: Exception | None = None
    delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e

            if attempt == max_attempts:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    attempts=max_attempts,
                    error=str(e)
                )
                raise RetryError(
                    f"Failed after {max_attempts} attempts: {e}",
                    last_exception=e
                ) from e

            # Calculate next delay with exponential backoff
            actual_delay = min(delay, max_delay)
            if jitter:
                actual_delay = actual_delay * (0.5 + random.random())

            logger.warning(
                "retry_attempt",
                function=func.__name__,
                attempt=attempt,
                max_attempts=max_attempts,
                delay=actual_delay,
                error=str(e)
            )

            await asyncio.sleep(actual_delay)
            delay *= backoff_factor

    # This should never be reached, but just in case
    raise RetryError(
        f"Failed after {max_attempts} attempts",
        last_exception=last_exception
    )
