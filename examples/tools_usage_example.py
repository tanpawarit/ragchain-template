"""
Example usage of tools with cachetools and rate limiting.

This example demonstrates how to use the tools with caching and rate limiting.
"""

import time

from src.tools.calculator import calculate_expression, fibonacci, multiply, statistics
from src.tools.utils.cache_manager import clear_cache, get_cache_stats


def main():
    """Main function to demonstrate tool usage."""
    print("=== Tools Usage Example with Cachetools ===\n")

    # Test calculator tools
    print("1. Testing Calculator Tools:")
    print("-" * 40)

    # Test multiply - using invoke method
    print("Testing multiply...")
    try:
        # Call the tool using invoke method
        result1 = multiply.invoke({"a": 5.0, "b": 10.0})
        print(f"multiply(5.0, 10.0) = {result1}")

        # Call again to test caching
        result2 = multiply.invoke({"a": 5.0, "b": 10.0})
        print(f"multiply(5.0, 10.0) [cached] = {result2}")

    except Exception as e:
        print(f"Error calling multiply: {e}")

    print()

    # Test calculate_expression
    print("Testing calculate_expression...")
    try:
        result = calculate_expression.invoke({"expression": "2 + 3 * 4"})
        print(f"calculate_expression('2 + 3 * 4') = {result}")

        # Test with different expression
        result = calculate_expression.invoke({"expression": "(10 + 5) / 3"})
        print(f"calculate_expression('(10 + 5) / 3') = {result}")

    except Exception as e:
        print(f"Error calling calculate_expression: {e}")

    print()

    # Test fibonacci
    print("Testing fibonacci...")
    try:
        # Test fibonacci with small numbers
        for n in [5, 10, 15]:
            start_time = time.time()
            result = fibonacci.invoke({"n": n})
            end_time = time.time()
            print(f"fibonacci({n}) = {result} (time: {end_time - start_time:.4f}s)")

        # Test calling the same number again (should be cached)
        start_time = time.time()
        result = fibonacci.invoke({"n": 10})
        end_time = time.time()
        print(f"fibonacci(10) [cached] = {result} (time: {end_time - start_time:.4f}s)")

    except Exception as e:
        print(f"Error calling fibonacci: {e}")

    print()

    # Test statistics
    print("Testing statistics...")
    try:
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        result = statistics.invoke({"numbers": numbers})
        print(f"statistics({numbers}):")
        print(f"  Count: {result['count']}")
        print(f"  Sum: {result['sum']}")
        print(f"  Mean: {result['mean']:.2f}")
        print(f"  Median: {result['median']}")
        print(f"  Min: {result['min']}")
        print(f"  Max: {result['max']}")
        print(f"  Std Dev: {result['std_dev']:.2f}")

        # Call again to test caching
        result2 = statistics.invoke({"numbers": numbers})
        print(f"  [Cached call] Mean: {result2['mean']:.2f}")

    except Exception as e:
        print(f"Error calling statistics: {e}")

    print()

    # Test rate limiting
    print("2. Testing Rate Limiting:")
    print("-" * 40)

    print("Testing rate limiting with multiply...")
    try:
        # Try to call the function multiple times quickly
        for i in range(3):
            result = multiply.invoke({"a": i + 1.0, "b": 2.0})
            print(f"Call {i + 1}: multiply({i + 1}, 2) = {result}")
            time.sleep(0.1)

        # Try to exceed rate limit
        print("Attempting to exceed rate limit...")
        try:
            for i in range(15):  # This should exceed the 10 calls/minute limit
                result = multiply.invoke({"a": i + 1.0, "b": 3.0})
                print(f"Rapid call {i + 1}: multiply({i + 1}, 3) = {result}")
        except RuntimeError as e:
            print(f"✓ Rate limit enforced: {e}")

    except Exception as e:
        print(f"Error testing rate limiting: {e}")

    print()

    # Show cache statistics
    print("3. Cache Statistics:")
    print("-" * 40)
    try:
        stats = get_cache_stats()
        print(f"Cache type: {stats['cache_type']}")
        print(f"Current size: {stats['current_size']}")
        print(f"Max size: {stats['max_size']}")
        print(f"TTL: {stats['ttl']} seconds")
    except Exception as e:
        print(f"Error getting cache stats: {e}")

    print()

    # Test cache clearing
    print("4. Cache Management:")
    print("-" * 40)
    try:
        print("Clearing cache...")
        clear_cache()
        print("Cache cleared!")

        # Show updated stats
        stats = get_cache_stats()
        print(f"Cache size after clearing: {stats['current_size']}")
    except Exception as e:
        print(f"Error clearing cache: {e}")

    print()

    # Test tool descriptions
    print("5. Tool Information:")
    print("-" * 40)

    tools = [
        multiply,
        calculate_expression,
        fibonacci,
        statistics,
    ]

    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Args: {tool.args}")
        print()

    print("=== Tools Example Complete ===")


if __name__ == "__main__":
    main()
