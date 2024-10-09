import pytest
from packg.caching import SimpleMemoryCache

def test_simple_memory_cache():
    cache = SimpleMemoryCache()
    cache_key = "test_key"
    result = cache.apply_memory_caching(cache_key, lambda x: x + 1, 1)
    assert result == 2
    cached_result = cache.apply_memory_caching(cache_key, lambda x: x + 1, 1)
    assert cached_result == 2  # Should return cached result, not recompute
