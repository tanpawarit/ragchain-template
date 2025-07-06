# Cache Manager Documentation

## Overview

Cache Manager uses `cachetools.TTLCache` as the main cache management system with automatic TTL (Time To Live) functionality.

## Features

- ✅ **TTL Cache**: Uses only `cachetools.TTLCache`
- ✅ **Automatic Expiration**: Cache expires automatically based on TTL
- ✅ **Thread Safe**: cachetools handles thread safety
- ✅ **Simple API**: Easy-to-use decorators
- ✅ **Production Ready**: Uses popular library (2.5k stars)

## Installation

```bash
uv add cachetools
```

## Quick Start

### 1. Simple Cache Decorator

```python
from src.tools.utils.cache_manager import simple_cache

@simple_cache(ttl=60, maxsize=100)
def expensive_function(x, y):
    # Expensive computation
    return x * y

# First call - computes result
result1 = expensive_function(5, 10)  # 50

# Second call - returns cached result
result2 = expensive_function(5, 10)  # 50 (from cache)
```

### 2. TTL Cache Decorator

```python
from src.tools.utils.cache_manager import cache_with_ttl

@cache_with_ttl(ttl=300, maxsize=50)
def api_call(url):
    # API call that should be cached for 5 minutes
    return requests.get(url).json()
```

### 3. LRU Cache (Built-in Python)

```python
from src.tools.utils.cache_manager import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## Cache Manager Class

```python
from src.tools.utils.cache_manager import CacheManager

# Create cache manager
cache = CacheManager(maxsize=100, ttl=600)

# Get stats
stats = cache.get_stats()
print(stats)  # {'cache_type': 'TTLCache', 'current_size': 0, 'max_size': 100, 'ttl': 600}

# Clear cache
cache.clear()
```

## Tools Usage

Calculator tools use cache decorators with rate limiting:

```python
from src.tools.calculator import multiply

# Tool with caching and rate limiting
result = multiply.invoke({"a": 5.0, "b": 10.0})
```

## Cache Information

### Get Cache Info

```python
# For decorated functions
@simple_cache(ttl=60, maxsize=10)
def my_function(x):
    return x * 2

# Get cache information
info = my_function.cache_info()
print(info)  # {'currsize': 1, 'maxsize': 10, 'ttl': 60}

# Clear specific function cache
my_function.cache_clear()
```

### Global Cache Stats

```python
from src.tools.utils.cache_manager import get_cache_stats, clear_cache

# Get global cache stats
stats = get_cache_stats()
print(stats)

# Clear global cache
clear_cache()
```

## Decorator Comparison

| Decorator | Library | TTL Support | LRU | Thread Safe | Use Case |
|-----------|---------|-------------|-----|-------------|----------|
| `@simple_cache` | cachetools | ✅ | ❌ | ✅ | General purpose with TTL |
| `@cache_with_ttl` | cachetools | ✅ | ❌ | ✅ | Explicit TTL focus |
| `@lru_cache` | functools | ❌ | ✅ | ✅ | Simple LRU, no TTL |

## Detailed Decorator Differences

### 1. Simple Cache vs Cache with TTL

**Key Generation:**
```python
# simple_cache - uses only arguments
@simple_cache(ttl=60)
def func1(x): return x * 2
@simple_cache(ttl=60)  
def func2(x): return x * 3
# func1(5) and func2(5) have SAME cache key! (collision risk)

# cache_with_ttl - includes function name
@cache_with_ttl(ttl=60)
def func1(x): return x * 2
@cache_with_ttl(ttl=60)
def func2(x): return x * 3  
# func1(5) and func2(5) have DIFFERENT cache keys (safer)
```

**Logging Behavior:**
```python
# simple_cache - includes debug logging
@simple_cache(ttl=60)
def multiply(a, b):
    return a * b
# Logs: "Cache hit for multiply" or "Cached result for multiply"

# cache_with_ttl - no logging (better performance)
@cache_with_ttl(ttl=60)
def api_call(url):
    return requests.get(url).json()
# No logging overhead
```

### 2. When to Use Each Decorator

**Use `@simple_cache` when:**
- You need debug information about cache hits/misses
- Development/testing phase
- Functions with unique argument patterns
- General purpose caching with logging

**Use `@cache_with_ttl` when:**
- Production performance is critical
- Multiple functions might have similar arguments
- You want to avoid cache key collisions
- Clean caching without debug output

**Use `@lru_cache` when:**
- You don't need TTL (cache never expires)
- Simple LRU eviction is sufficient
- Maximum compatibility (built into Python)
- Memory usage is more important than time-based expiration

### 3. Performance Comparison

```python
import time

# Performance test
@simple_cache(ttl=300)
def test_simple(x):
    return x * 2

@cache_with_ttl(ttl=300)
def test_ttl(x):
    return x * 2

# cache_with_ttl is slightly faster due to no logging
# simple_cache provides better debugging capabilities
```

## Configuration Options

### TTL (Time To Live)
- **Default**: 300 seconds (5 minutes)
- **Range**: 1 second to unlimited
- **Usage**: `ttl=60` for 1 minute cache

### Max Size
- **Default**: 128 entries
- **Range**: 1 to unlimited
- **Usage**: `maxsize=50` for 50 cache entries

## Best Practices

### 1. Choose Right TTL
```python
# Fast changing data - short TTL
@simple_cache(ttl=30)  # 30 seconds
def get_stock_price(symbol):
    return fetch_stock_price(symbol)

# Slow changing data - long TTL  
@simple_cache(ttl=3600)  # 1 hour
def get_user_profile(user_id):
    return fetch_user_profile(user_id)
```

### 2. Appropriate Cache Size
```python
# Small dataset - small cache
@simple_cache(ttl=300, maxsize=10)
def get_config(key):
    return fetch_config(key)

# Large dataset - larger cache
@simple_cache(ttl=600, maxsize=1000)
def get_product_info(product_id):
    return fetch_product_info(product_id)
```

### 3. Cache Key Considerations
- All arguments are used to create cache key
- Non-serializable objects will use `str()` representation
- Be careful with mutable arguments

```python
@simple_cache(ttl=300)
def process_data(data_list):
    # Warning: if data_list changes content but same object
    # cache key will be the same but results may differ
    return sum(data_list)

# Better: use immutable types
@simple_cache(ttl=300)
def process_data(data_tuple):
    return sum(data_tuple)
```

### 4. Avoiding Cache Collisions

```python
# ❌ BAD: Potential collision with simple_cache
@simple_cache(ttl=60)
def get_user_by_id(user_id):
    return fetch_user(user_id)

@simple_cache(ttl=60)
def get_product_by_id(product_id):
    return fetch_product(product_id)
# If user_id == product_id, cache collision occurs!

# ✅ GOOD: Use cache_with_ttl for different function types
@cache_with_ttl(ttl=60)
def get_user_by_id(user_id):
    return fetch_user(user_id)

@cache_with_ttl(ttl=60)
def get_product_by_id(product_id):
    return fetch_product(product_id)
# Function names included in cache key - no collision
```

## Performance Tips

### 1. Monitor Cache Hit Rate
```python
@simple_cache(ttl=300, maxsize=100)
def expensive_function(x):
    return complex_computation(x)

# Check performance
info = expensive_function.cache_info()
hit_rate = info['currsize'] / (info['currsize'] + info.get('misses', 0))
print(f"Cache hit rate: {hit_rate:.2%}")
```

### 2. Adjust Cache Size Based on Usage
```python
# Start small and monitor
@simple_cache(ttl=300, maxsize=50)
def my_function(x):
    return expensive_operation(x)

# If cache is always full, increase size
# If cache is mostly empty, decrease size
```

### 3. Use Different TTL for Different Data Types
```python
# Real-time data
@simple_cache(ttl=10)
def get_live_data():
    return fetch_live_data()

# Reference data  
@simple_cache(ttl=3600)
def get_reference_data():
    return fetch_reference_data()
```

### 4. Debug Cache Behavior

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# simple_cache will show cache hit/miss messages
@simple_cache(ttl=60)
def debug_function(x):
    return x * 2

# cache_with_ttl won't show any cache messages
@cache_with_ttl(ttl=60)
def silent_function(x):
    return x * 3
```

## Example: Complete Tool with Cache

```python
from langchain_core.tools import tool
from src.tools.utils.cache_manager import simple_cache
from src.tools.utils.rate_limiter import rate_limit

@tool
@simple_cache(ttl=300, maxsize=100)  # Cache for 5 minutes
@rate_limit(max_calls=10, time_window=60)  # 10 calls per minute
def api_call_tool(endpoint: str, params: dict) -> dict:
    """
    Make API call with caching and rate limiting.
    
    Args:
        endpoint: API endpoint URL
        params: Request parameters
        
    Returns:
        API response data
    """
    response = requests.get(endpoint, params=params)
    return response.json()
```

## Troubleshooting

### Common Issues

1. **Cache not working**: Check that arguments are exactly the same
2. **Memory usage**: Reduce `maxsize` or `ttl`
3. **Stale data**: Reduce `ttl` or use `cache_clear()`
4. **Cache collisions**: Use `cache_with_ttl` for different function types

### Debug Cache Behavior

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will show cache hit/miss messages
@simple_cache(ttl=60)
def debug_function(x):
    return x * 2
```

## Migration from Old Cache

If you have old code using `SimpleCacheManager`:

```python
# Old code
from src.tools.utils.cache_manager import SimpleCacheManager

# New code  
from src.tools.utils.cache_manager import CacheManager
```

The API remains the same, just using TTLCache only. 