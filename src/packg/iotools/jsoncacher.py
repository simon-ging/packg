from __future__ import annotations

import json
from collections.abc import KeysView
from pathlib import Path
from typing import Any

from loguru import logger

from packg.tqdmext import tqdm_max_ncols


class JSONCacher:
    def __init__(self, cache_file: str, verbose: bool = True):
        """Initialize JSONCacher with a cache file path.

        Args:
            cache_file: Path to the cache file where all JSON data will be stored
            verbose: Whether to enable verbose logging
        """
        self.cache_file = Path(cache_file)
        self.verbose = verbose
        self.cache: dict[str, dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        """Load the cache from file if it exists."""
        if self.cache_file.exists():
            with self.cache_file.open("r") as f:
                return json.load(f)
        # Create empty cache file if it doesn't exist
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_file.open("w") as f:
            json.dump({}, f)
        return {}

    def _save_cache(self):
        """Save the cache to file."""
        with self.cache_file.open("w") as f:
            json.dump(self.cache, f, indent=2)

    def update_from_directory(self, directory: str):
        """Update cache with JSON files from directory.

        Args:
            directory: Root directory to search for JSON files
        """
        if self.verbose:
            logger.info(f"Updating cache from directory: {directory}")

        directory_path = Path(directory)
        json_files = list(directory_path.rglob("*.json"))
        cache_abs_path = self.cache_file.resolve()

        # Keep track of existing files to detect deletions
        found_keys = set()
        updated_count = 0
        deleted_count = 0

        pbar = tqdm_max_ncols(
            total=len(json_files), desc="Updating JSON file cache", disable=not self.verbose
        )
        for json_file in json_files:
            # Skip the cache file itself
            if json_file.resolve() == cache_abs_path:
                continue

            rel_path = json_file.relative_to(directory_path)
            cache_key = rel_path.as_posix()[:-5]
            found_keys.add(cache_key)

            # Get file modification time
            mod_time = json_file.stat().st_mtime

            # Only update if file is new or modified
            if cache_key not in self.cache or self.cache[cache_key]["mod_time"] < mod_time:
                with json_file.open("r") as f:
                    data = json.load(f)
                self.cache[cache_key] = {"data": data, "mod_time": mod_time}
                updated_count += 1
            pbar.update(1)
        pbar.close()
        # Remove entries for deleted files
        deleted_keys = set(self.cache.keys()) - found_keys
        for key in deleted_keys:
            del self.cache[key]
            deleted_count += 1

        self._save_cache()

        if self.verbose:
            logger.info(
                f"Cache update complete. Updated: {updated_count}, Deleted: {deleted_count}, Total files: {len(found_keys)}"
            )

    def get(self, key: str, raise_missing: bool = False) -> Any:
        """Get data for a specific key.

        Args:
            key: The key to retrieve (relative path without .json extension)

        Returns:
            The cached data if it exists, None otherwise
        """
        if key in self.cache:
            return self.cache[key]["data"]
        if raise_missing:
            raise KeyError(f"Key {key} not found in cache")
        return None

    def __getitem__(self, key: str) -> Any:
        return self.get(key, raise_missing=True)

    def __len__(self) -> int:
        return len(self.cache)

    def items_dict(self) -> dict[str, Any]:
        """Get all cached data.

        Returns:
            Dictionary mapping keys to their data
        """
        return {k: v["data"] for k, v in self.cache.items()}

    def keys(self) -> KeysView[str]:
        """Get all keys in the cache."""
        return self.cache.keys()
