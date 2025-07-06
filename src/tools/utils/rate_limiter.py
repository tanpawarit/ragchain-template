"""
Rate limiter utility for tools.

Provides rate limiting functionality to prevent tools from being called too frequently.
Supports both sync and async functions with configurable limits and time windows.
"""

import asyncio
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Any, Callable, Dict, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter class for tracking and enforcing call limits."""

    def __init__(self, max_calls: int = 10, time_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()

    def _get_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate a unique key for the function call."""
        func_name = getattr(func, "__name__", str(func))
        # Simple key based on function name - can be enhanced with args/kwargs
        return f"{func_name}"

    def _cleanup_old_calls(self, key: str, current_time: float) -> None:
        """Remove old calls outside the time window."""
        while self.calls[key] and current_time - self.calls[key][0] > self.time_window:
            self.calls[key].popleft()

    async def is_allowed(self, func: Callable, args: tuple, kwargs: dict) -> bool:
        """
        Check if a function call is allowed based on rate limits.

        Args:
            func: Function being called
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            True if call is allowed, False otherwise
        """
        async with self.lock:
            key = self._get_key(func, args, kwargs)
            current_time = time.time()

            # Clean up old calls
            self._cleanup_old_calls(key, current_time)

            # Check if we're within limits
            if len(self.calls[key]) >= self.max_calls:
                logger.warning(
                    f"Rate limit exceeded for {key}: {len(self.calls[key])}/{self.max_calls} calls"
                )
                return False

            # Record this call
            self.calls[key].append(current_time)
            return True

    def is_allowed_sync(self, func: Callable, args: tuple, kwargs: dict) -> bool:
        """
        Synchronous version of is_allowed for sync functions.

        Args:
            func: Function being called
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            True if call is allowed, False otherwise
        """
        key = self._get_key(func, args, kwargs)
        current_time = time.time()

        # Clean up old calls
        self._cleanup_old_calls(key, current_time)

        # Check if we're within limits
        if len(self.calls[key]) >= self.max_calls:
            logger.warning(
                f"Rate limit exceeded for {key}: {len(self.calls[key])}/{self.max_calls} calls"
            )
            return False

        # Record this call
        self.calls[key].append(current_time)
        return True

    def get_stats(self, func: Callable) -> Dict[str, Any]:
        """Get statistics for a function."""
        key = self._get_key(func, (), {})
        current_time = time.time()
        self._cleanup_old_calls(key, current_time)

        return {
            "function": key,
            "current_calls": len(self.calls[key]),
            "max_calls": self.max_calls,
            "time_window": self.time_window,
            "remaining_calls": max(0, self.max_calls - len(self.calls[key])),
        }


# Global rate limiter instance
_default_rate_limiter = RateLimiter()


def rate_limit(
    max_calls: int = 10,
    time_window: int = 60,
    rate_limiter: Optional[RateLimiter] = None,
):
    """
    Decorator to add rate limiting to functions.

    Args:
        max_calls: Maximum number of calls allowed in time window
        time_window: Time window in seconds
        rate_limiter: Custom rate limiter instance (optional)

    Returns:
        Decorated function with rate limiting
    """
    limiter = rate_limiter or RateLimiter(max_calls, time_window)

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not await limiter.is_allowed(func, args, kwargs):
                    raise RuntimeError(f"Rate limit exceeded for {func.__name__}")
                return await func(*args, **kwargs)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not limiter.is_allowed_sync(func, args, kwargs):
                    raise RuntimeError(f"Rate limit exceeded for {func.__name__}")
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator


def get_rate_limiter_stats(
    func: Callable, rate_limiter: Optional[RateLimiter] = None
) -> Dict[str, Any]:
    """
    Get rate limiter statistics for a function.

    Args:
        func: Function to get stats for
        rate_limiter: Rate limiter instance (optional)

    Returns:
        Dictionary with rate limiter statistics
    """
    limiter = rate_limiter or _default_rate_limiter
    return limiter.get_stats(func)


# Example usage functions
async def example_async_function():
    """Example async function with rate limiting."""
    await asyncio.sleep(0.1)
    return "async result"


def example_sync_function():
    """Example sync function with rate limiting."""
    time.sleep(0.1)
    return "sync result"


# Apply rate limiting to examples
rate_limited_async = rate_limit(max_calls=5, time_window=60)(example_async_function)
rate_limited_sync = rate_limit(max_calls=3, time_window=30)(example_sync_function)
