import os
import pickle
import time

import joblib
from joblib import register_store_backend
from joblib._store_backends import FileSystemStoreBackend  # noqa
from joblib.logger import format_time

from packg.paths import get_packg_cache_dir


class StoreNoNumpy(FileSystemStoreBackend):
    """
    Backend for joblib with pickle instead of numpy_pickle.
    Faster than the original backend for non-numpy objects (e.g. dicts).
    """

    NAME = "no_numpy"

    def load_item(self, call_id, verbose=1, timestamp=None, metadata=None):
        """Load an item from the store given its id as a list of str."""
        full_path = os.path.join(self.location, *call_id)

        if verbose > 1:
            ts_string = (
                f"{format_time(time.time() - timestamp): <16}" if timestamp is not None else ""
            )
            signature = os.path.basename(call_id[0])
            if metadata is not None and "input_args" in metadata:
                kwargs = ", ".join(f"{k}={v}" for k, v in metadata["input_args"].items())
                signature += f"({kwargs})"
            msg = f"[Memory]{ts_string}: Loading {signature}"
            if verbose < 10:
                print(f"{msg}...")
            else:
                print(f"{msg} from {full_path}")

        mmap_mode = None if not hasattr(self, "mmap_mode") else self.mmap_mode

        filename = os.path.join(full_path, "output.pkl")
        if not self._item_exists(filename):
            raise KeyError(
                "Non-existing item (may have been " f"cleared).\nFile {filename} does not exist"
            )

        assert mmap_mode is None, "Standard pickle does not support mmap_mode"
        with self._open_item(filename, "rb") as fh:
            item = pickle.load(fh)
        return item


register_store_backend(StoreNoNumpy.NAME, StoreNoNumpy)


def get_joblib_memory(
    location=get_packg_cache_dir() / "joblib", verbose=1, numpy_capable=False
) -> joblib.Memory:
    """
    Wrapper for joblib.Memory which uses the StoreNoNumpy backend by default.

    Args:
        location: cache dir
        verbose: higher = more verbose
        numpy_capable: keep False unless needed, it makes loading alot slower for e.g. dicts

    Returns:
        memory: use as @memory.cache decorator for functions
    """
    backend = "local" if numpy_capable else StoreNoNumpy.NAME
    return joblib.Memory(location=location, backend=backend, verbose=verbose)


class SimpleMemoryCache:
    """
    Cache objects in memory.

    Usage:
        # given a function to cache e.g. load_json(file)
        # create cache and call the function with it
        memory_cache = SimpleMemoryCache()
        cache_key = "some_cache_key"
        data = memory_cache.apply_memory_caching(cache_key, load_json, file)
        data_again = memory_cache.apply_memory_caching(cache_key, load_json, file)
        # Function is called once, then data is loaded from memory since cache_key exists.
    """

    def __init__(self):
        self._cache_dict = {}

    def apply_memory_caching(self, cache_key, func, *args, **kwargs):
        cache_dict = self._cache_dict
        if cache_key is None:
            cache_key = joblib.hash((args, kwargs))
        if cache_key not in cache_dict:
            func_result = func(*args, **kwargs)
            cache_dict[cache_key] = func_result
        return cache_dict[cache_key]

    def _load_from_memory_cache(self, cache_key):
        cache_dict = self._cache_dict
        if cache_key not in cache_dict:
            return None
        return cache_dict[cache_key]

    def _write_to_memory_cache(self, cache_key, obj):
        cache_dict = self._cache_dict
        cache_dict[cache_key] = obj


memory_cache = SimpleMemoryCache()
