import os
import pickle
import tempfile
from pathlib import Path

import pytest

from packg.caching import SimpleMemoryCache, get_joblib_memory, memory_cache


def test_get_joblib_memory():
    # Test with default parameters (no_numpy backend)
    memory = get_joblib_memory()
    assert memory.backend == "no_numpy"

    # Test with numpy_capable=True (local backend)
    memory_numpy = get_joblib_memory(numpy_capable=True)
    assert memory_numpy.backend == "local"

    # Test with custom location
    with tempfile.TemporaryDirectory() as temp_dir:
        memory_custom = get_joblib_memory(location=temp_dir)
        assert str(memory_custom.location).endswith(os.path.basename(temp_dir))

        # Test caching with custom location
        @memory_custom.cache
        def example_func(x):
            return x * 2

        # First call should compute
        result1 = example_func(5)
        assert result1 == 10

        # Second call should use cache
        result2 = example_func(5)
        assert result2 == 10
        assert result1 is result2  # Should be the same object


def test_simple_memory_cache():
    cache = SimpleMemoryCache()

    # Test function to cache
    def example_func(x, y):
        return x + y

    # Test with explicit cache key
    result1 = cache.apply_memory_caching("test_key", example_func, 1, 2)
    assert result1 == 3

    # Test cache hit
    result2 = cache.apply_memory_caching("test_key", example_func, 1, 2)
    assert result2 == 3
    assert result1 is result2  # Should be the same object

    # Test with auto-generated cache key
    result3 = cache.apply_memory_caching(None, example_func, 2, 3)
    assert result3 == 5

    # Test direct cache access methods
    cache._write_to_memory_cache("direct_key", "test_value")
    assert cache._load_from_memory_cache("direct_key") == "test_value"
    assert cache._load_from_memory_cache("nonexistent_key") is None


def test_global_memory_cache():
    # Test the global memory_cache instance
    def example_func(x):
        return x * 2

    result1 = memory_cache.apply_memory_caching("global_test", example_func, 5)
    assert result1 == 10

    # Test cache hit
    result2 = memory_cache.apply_memory_caching("global_test", example_func, 5)
    assert result2 == 10
    assert result1 is result2  # Should be the same object
