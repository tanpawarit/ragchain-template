"""
Cache manager utility using cachetools TTLCache.

Provides easy-to-use caching functionality with TTL support.
"""

import functools
import hashlib
import json
import time
from typing import Any, Callable, Dict, Optional

from cachetools import TTLCache

from src.utils.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """
    Cache manager using cachetools TTLCache.

    Simple and efficient caching with automatic TTL expiration.
    """

    def __init__(self, maxsize: int = 128, ttl: int = 300):
        """
        Initialize cache manager.

        Args:
            maxsize: Maximum number of cache entries
            ttl: Time to live in seconds
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.cache_type = "TTLCache"

        logger.info(f"Initialized TTLCache with maxsize={maxsize}, ttl={ttl}")

    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function and arguments."""
        func_name = getattr(func, "__name__", str(func))

        try:
            # Create JSON representation for consistent hashing
            args_str = json.dumps(args, sort_keys=True, default=str)
            kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
            key_data = f"{func_name}:{args_str}:{kwargs_str}"
        except (TypeError, ValueError):
            # Fallback for non-serializable objects
            key_data = f"{func_name}:{str(args)}:{str(kwargs)}"

        # Use first 16 characters of SHA256 hash
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, func: Callable, args: tuple, kwargs: dict) -> Optional[Any]:
        """Get cached result."""
        key = self._generate_key(func, args, kwargs)
        return self.cache.get(key)

    def set(self, func: Callable, args: tuple, kwargs: dict, value: Any) -> None:
        """Store result in cache."""
        key = self._generate_key(func, args, kwargs)
        self.cache[key] = value

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_type": self.cache_type,
            "current_size": self.cache.currsize,
            "max_size": self.cache.maxsize,
            "ttl": self.ttl,
        }


# Global cache instance
_default_cache = CacheManager()


def simple_cache(ttl: int = 300, maxsize: int = 128):
    """
    Simple cache decorator using cachetools TTLCache.

    Args:
        ttl: Time to live in seconds
        maxsize: Maximum cache size

    Example:
        @simple_cache(ttl=60, maxsize=100)
        def expensive_function(x, y):
            return x * y
    """

    def decorator(func: Callable) -> Callable:
        cache = TTLCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate key
            key_data = f"{args}:{kwargs}"
            key = hashlib.sha256(key_data.encode()).hexdigest()[:16]

            # Try cache first
            if key in cache:
                logger.debug(f"Cache hit for {func.__name__}")
                return cache[key]

            # Call function and cache result
            result = func(*args, **kwargs)
            cache[key] = result
            logger.debug(f"Cached result for {func.__name__}")
            return result

        # Add cache management methods
        setattr(wrapper, "cache_clear", cache.clear)
        setattr(
            wrapper,
            "cache_info",
            lambda: {
                "currsize": cache.currsize,
                "maxsize": maxsize,
                "ttl": ttl,
            },
        )

        return wrapper

    return decorator


def lru_cache(maxsize: int = 128):
    """
    Simple LRU cache decorator using functools.lru_cache.

    This is the simplest option - built into Python!

    Args:
        maxsize: Maximum cache size

    Example:
        @lru_cache(maxsize=100)
        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
    """
    return functools.lru_cache(maxsize=maxsize)


def cache_with_ttl(ttl: int = 300, maxsize: int = 128):
    """
    Cache decorator with TTL support using cachetools.

    Args:
        ttl: Time to live in seconds
        maxsize: Maximum cache size

    Example:
        @cache_with_ttl(ttl=60, maxsize=50)
        def get_weather(city):
            return fetch_weather_api(city)
    """

    def decorator(func: Callable) -> Callable:
        cache = TTLCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate key
            key_data = f"{func.__name__}:{args}:{kwargs}"
            key = hashlib.sha256(key_data.encode()).hexdigest()[:16]

            # Try cache first
            if key in cache:
                return cache[key]

            # Call function and cache result
            result = func(*args, **kwargs)
            cache[key] = result
            return result

        setattr(wrapper, "cache_clear", cache.clear)
        setattr(
            wrapper,
            "cache_info",
            lambda: {
                "currsize": cache.currsize,
                "maxsize": maxsize,
                "ttl": ttl,
            },
        )
        return wrapper

    return decorator


# Legacy decorator for backward compatibility
def cache_result(ttl: int = 300, cache_manager: Optional[CacheManager] = None):
    """
    Legacy cache decorator for backward compatibility.

    Args:
        ttl: Time to live in seconds
        cache_manager: Optional cache manager instance

    Example:
        @cache_result(ttl=60)
        def expensive_function(x, y):
            return x * y
    """
    return simple_cache(ttl=ttl, maxsize=128)


# Example usage functions
@simple_cache(ttl=60, maxsize=50)
def example_cached_function(x: int, y: int) -> int:
    """Example function with simple caching."""
    logger.info(f"Computing {x} * {y}")
    time.sleep(0.1)  # Simulate expensive computation
    return x * y


@lru_cache(maxsize=100)
def example_lru_function(n: int) -> int:
    """Example function with LRU caching."""
    logger.info(f"Computing fibonacci({n})")
    if n < 2:
        return n
    return example_lru_function(n - 1) + example_lru_function(n - 2)


@cache_with_ttl(ttl=30, maxsize=20)
def example_ttl_function(text: str) -> str:
    """Example function with TTL caching."""
    logger.info(f"Processing text: {text}")
    time.sleep(0.1)  # Simulate expensive computation
    return text.upper()


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for the default cache."""
    return _default_cache.get_stats()


def clear_cache() -> None:
    """Clear the default cache."""
    _default_cache.clear()


if __name__ == "__main__":
    # Example usage
    print("Testing TTL cache...")

    # Test simple cache
    result1 = example_cached_function(5, 10)
    result2 = example_cached_function(5, 10)  # Should be cached
    print(f"Results: {result1}, {result2}")

    # Test LRU cache
    fib_result = example_lru_function(10)
    print(f"Fibonacci(10): {fib_result}")

    # Test TTL cache
    text_result = example_ttl_function("hello world")
    print(f"Text result: {text_result}")

    # Print cache stats
    print(f"Cache stats: {get_cache_stats()}")
