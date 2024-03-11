import os
import re
import shutil
from pathlib import Path

import pytest

from packg.iotools.file_indexer import regex_glob


@pytest.fixture(scope="module")
def test_dir(tmp_path_factory):
    """Creates a temporary test directory with sample files."""
    test_dir = tmp_path_factory.mktemp("test_dir")
    (test_dir / "file1.txt").touch()
    (test_dir / "file2.log").touch()
    (test_dir / "data.csv").touch()
    os.makedirs(test_dir / "subdir")
    (test_dir / "subdir" / "other_file.txt").touch()
    yield test_dir
    shutil.rmtree(test_dir)


def test_basic_regex_filter(test_dir):
    results = list(regex_glob(test_dir, r".*\.txt$", return_relative_paths=True))
    assert len(results) == 2
    assert Path("file1.txt") in results
    assert Path("subdir/other_file.txt") in results


def test_filename_only_match(test_dir):
    results = list(
        regex_glob(test_dir, r"data", match_filename_only=True, return_relative_paths=True)
    )
    assert len(results) == 1
    assert Path("data.csv") in results


def test_inverse_match(test_dir):
    results = list(
        regex_glob(test_dir, r".*\.txt$", match_inverse=True, return_relative_paths=True)
    )
    assert len(results) == 3
    assert Path("file2.log") in results
    assert Path("data.csv") in results
    assert Path("subdir") in results


def test_inverse_match_ignore_dirs(test_dir):
    results = list(
        regex_glob(
            test_dir,
            r".*\.txt$",
            match_inverse=True,
            ignore_directories=True,
            return_relative_paths=True,
        )
    )
    assert len(results) == 2
    assert Path("file2.log") in results
    assert Path("data.csv") in results


def test_non_relative_paths(test_dir):
    results = list(regex_glob(test_dir, r"\.csv$", return_relative_paths=False))
    assert len(results) == 1
    assert test_dir / "data.csv" in results


def test_posix_string_return(test_dir):
    results = list(regex_glob(test_dir, r".*", return_as_posix_str=True))
    assert all(isinstance(p, str) for p in results)


def test_glob_pattern(test_dir):
    results = list(regex_glob(test_dir, r".*", glob_pattern="**/*.txt"))
    assert len(results) == 2


def test_invalid_regex(test_dir):
    with pytest.raises(re.error):
        # note how generator must be turned into list in order to run and trigger the error.
        list(regex_glob(test_dir, "[invalid_pattern"))
