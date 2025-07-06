"""
Calculator tools with caching using cachetools.

Production-ready tools that combine @tool decorator with caching utilities.
"""

import time
from typing import List

from langchain_core.tools import tool

from src.tools.utils.cache_manager import cache_with_ttl, lru_cache, simple_cache
from src.tools.utils.rate_limiter import rate_limit
from src.utils.logger import get_logger

logger = get_logger(__name__)


@tool
@simple_cache(ttl=300, maxsize=100)  # Cache for 5 minutes
@rate_limit(max_calls=10, time_window=60)  # 10 calls per minute
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers with caching and rate limiting.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b
    """
    logger.info(f"Computing {a} * {b}")
    time.sleep(0.1)  # Simulate some computation time
    return a * b


@tool
@cache_with_ttl(ttl=600)  # Cache for 10 minutes
@rate_limit(max_calls=5, time_window=60)  # 5 calls per minute
def calculate_expression(expression: str) -> float:
    """
    Safely evaluate a mathematical expression with caching and rate limiting.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")

    Returns:
        Result of the mathematical expression

    Raises:
        ValueError: If expression is invalid or contains forbidden operations
    """
    logger.info(f"Evaluating expression: {expression}")

    # Security: Only allow safe mathematical operations
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        raise ValueError("Expression contains forbidden characters")

    # Additional security: prevent function calls
    forbidden_words = ["import", "exec", "eval", "__", "lambda"]
    if any(word in expression.lower() for word in forbidden_words):
        raise ValueError("Expression contains forbidden operations")

    try:
        # Simulate computation time
        time.sleep(0.1)
        result = eval(expression)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid mathematical expression: {e}")


# Create a separate fibonacci function without @tool decorator for recursion
@lru_cache(maxsize=50)  # Simple LRU cache
def _fibonacci_helper(n: int) -> int:
    """Helper function for fibonacci calculation with caching."""
    if n <= 1:
        return n
    return _fibonacci_helper(n - 1) + _fibonacci_helper(n - 2)


@tool
def fibonacci(n: int) -> int:
    """
    Calculate Fibonacci number with LRU caching for performance.

    Args:
        n: Position in Fibonacci sequence (must be non-negative)

    Returns:
        Fibonacci number at position n

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    logger.info(f"Computing Fibonacci({n})")

    # Use cached helper function
    return _fibonacci_helper(n)


@tool
@simple_cache(ttl=180, maxsize=30)  # Cache for 3 minutes
@rate_limit(max_calls=20, time_window=60)  # 20 calls per minute
def statistics(numbers: List[float]) -> dict:
    """
    Calculate comprehensive statistics for a list of numbers.

    Args:
        numbers: List of numbers to analyze

    Returns:
        Dictionary containing various statistics

    Raises:
        ValueError: If numbers list is empty
    """
    if not numbers:
        raise ValueError("Numbers list cannot be empty")

    logger.info(f"Computing statistics for {len(numbers)} numbers")

    # Simulate computation time
    time.sleep(0.05)

    sorted_numbers = sorted(numbers)
    n = len(numbers)

    # Calculate statistics
    total = sum(numbers)
    mean = total / n

    # Median
    if n % 2 == 0:
        median = (sorted_numbers[n // 2 - 1] + sorted_numbers[n // 2]) / 2
    else:
        median = sorted_numbers[n // 2]

    # Variance and standard deviation
    variance = sum((x - mean) ** 2 for x in numbers) / n
    std_dev = variance**0.5

    return {
        "count": n,
        "sum": total,
        "mean": mean,
        "median": median,
        "min": min(numbers),
        "max": max(numbers),
        "range": max(numbers) - min(numbers),
        "variance": variance,
        "std_dev": std_dev,
        "sorted": sorted_numbers,
    }


# Export all calculator tools
__all__ = [
    "multiply",
    "calculate_expression",
    "fibonacci",
    "statistics",
]
