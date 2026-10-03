"""
Index folders and hash their files, both cached as json in the packg cache dir.
"""

import hashlib
import os
import time
from pathlib import Path

from loguru import logger

from packg.iotools import dump_json, load_json, yield_chunked_bytes
from packg.iotools.file_indexer import FileProperties, make_index
from packg.paths import get_packg_cache_dir
from packg.strings import b64_encode_from_bytes, quote_with_urlparse
from packg.typext import PathType


def get_file_hash_b64(file_path: PathType, chunk_size=1024 * 1024) -> str:
    """Compute hash of the file specified by file_path, return as b64 string."""
    return b64_encode_from_bytes(get_file_hash(file_path, chunk_size=chunk_size), strip_equals=True)


def get_file_hash(file_path: PathType, chunk_size=1024 * 1024) -> bytes:
    """Compute hash of the file specified by file_path."""
    hasher = hashlib.blake2b()
    for byte_block in yield_chunked_bytes(file_path, chunk_size=chunk_size):
        hasher.update(byte_block)

    return hasher.digest()


def get_folder_index_cache_file(folder: PathType, suffix="json") -> Path:
    folder_safe = quote_with_urlparse(Path(folder).absolute().as_posix())
    return get_packg_cache_dir() / "file_paths" / f"{folder_safe}.{suffix}"


def make_index_cached(
    folder: PathType,
    cache_max_age_seconds: float = 3600 * 24 * 7,
    reset_cache: bool = False,
) -> dict[str, FileProperties]:
    folder = Path(folder)
    cache_file = get_folder_index_cache_file(folder)
    index = None
    if not reset_cache and cache_file.is_file():
        logger.info(f"Loading cache from {cache_file} for {folder}")
        data = load_json(cache_file)
        created_timestamp = data["created_timestamp"]
        current_timestamp = time.time()
        delta = current_timestamp - created_timestamp
        if delta < cache_max_age_seconds:
            index = data["index"]
            index = {k: FileProperties(**v) for k, v in index.items()}

    if index is None:
        start_ts = time.time()
        index = make_index(folder)
        index = dict(sorted(index.items(), key=lambda x: x[0]))
        data = dict(created_timestamp=start_ts, index=index)
        dump_json(data, cache_file, create_parent=True)
    return index


class FolderHashCache:
    """
    Hashes of the files of one folder, kept in a json file between runs. An entry is only
    reused while size and mtime of the file are the ones it was computed for, so a file that
    changed is hashed again instead of being compared by its old content.
    """

    def __init__(self, src, reset_cache=False):
        self.src = Path(src)
        self.cache_file = get_folder_index_cache_file(src, suffix="hashes.json")
        # file name relative to the folder -> [size, mtime in ns, hash]
        self.hashes: dict[str, list] = {}
        self.n_new = 0
        if self.cache_file.is_file() and not reset_cache:
            self.hashes = load_json(self.cache_file)
            logger.info(f"Reloaded {len(self.hashes)} hashes from {self.cache_file}")

    def get_hash(self, filename):
        stat = (self.src / filename).stat()
        entry = self.hashes.get(filename)
        if entry is not None and entry[:2] == [stat.st_size, stat.st_mtime_ns]:
            return entry[2]
        file_hash = get_file_hash_b64(self.src / filename)
        self.hashes[filename] = [stat.st_size, stat.st_mtime_ns, file_hash]
        self.n_new += 1
        return file_hash

    def write_new_hashes(self):
        if self.n_new == 0:
            return
        # written next to the target and renamed, so an interrupted run leaves no broken cache
        part_file = self.cache_file.with_name(f"{self.cache_file.name}.part")
        dump_json(self.hashes, part_file, create_parent=True)
        os.replace(part_file, self.cache_file)
        logger.info(f"Wrote {len(self.hashes)} hashes ({self.n_new} new) to {self.cache_file}")
        self.n_new = 0
