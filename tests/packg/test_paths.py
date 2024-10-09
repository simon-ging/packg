from packg.paths import (
    get_data_dir,
    get_cache_dir,
)


def test_paths():
    # todo test setting env vars with pytest
    # todo set overwrite_dir param and check results
    print(f"data_dir={get_data_dir()}")
    print(f"cache_dir={get_cache_dir()}")
    assert True
import pytest
from packg.paths import get_cache_dir, get_data_dir

def test_get_cache_dir():
    cache_dir = get_cache_dir()
    assert cache_dir.exists()

def test_get_data_dir():
    data_dir = get_data_dir()
    assert data_dir.exists()
