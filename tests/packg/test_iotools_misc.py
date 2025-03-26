import os
import pytest
from pathlib import Path
from packg.iotools.misc import (
    set_working_directory,
    get_file_size,
    get_file_size_in_mb,
    format_b_in_mb,
    format_b_in_gb,
    format_bytes_human_readable,
)


def test_set_working_directory(tmp_path):
    # Create a test directory
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Create a test file in the test directory
    test_file = test_dir / "test.txt"
    test_file.write_text("test content")

    # Get the original working directory
    original_dir = Path(os.getcwd()).absolute()

    # Test the context manager
    with set_working_directory(test_dir):
        # Verify we're in the test directory
        assert Path(os.getcwd()).absolute() == test_dir.absolute()
        # Verify we can access the test file
        assert test_file.read_text() == "test content"

    # Verify we're back in the original directory
    assert Path(os.getcwd()).absolute() == original_dir


def test_get_file_size(tmp_path):
    # Create a test file with known size
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    file_size = test_file.stat().st_size

    # Test different scales
    assert get_file_size(test_file, scale=0) == file_size  # B
    assert get_file_size(test_file, scale=1) == file_size / 1024  # KB
    assert get_file_size(test_file, scale=2) == file_size / 1024**2  # MB
    assert get_file_size(test_file, scale=3) == file_size / 1024**3  # GB


def test_get_file_size_in_mb(tmp_path):
    # Create a test file with known size
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    file_size = test_file.stat().st_size

    # Test conversion to MB
    assert get_file_size_in_mb(test_file) == file_size / 1024**2


def test_format_b_in_mb():
    # Test various sizes
    assert format_b_in_mb(1024**2) == "1.000MB"
    assert format_b_in_mb(2 * 1024**2) == "2.000MB"
    assert format_b_in_mb(1024**2 / 2) == "0.500MB"


def test_format_b_in_gb():
    # Test various sizes
    assert format_b_in_gb(1024**3) == "1.000GB"
    assert format_b_in_gb(2 * 1024**3) == "2.000GB"
    assert format_b_in_gb(1024**3 / 2) == "0.500GB"


def test_format_bytes_human_readable():
    # Test various sizes and units
    assert format_bytes_human_readable(1024**0) == "1.000B"
    assert format_bytes_human_readable(1024**1) == "1.000KB"
    assert format_bytes_human_readable(1024**2) == "1.000MB"
    assert format_bytes_human_readable(1024**3) == "1.000GB"
    assert format_bytes_human_readable(1024**4) == "1.000TB"

    # Test intermediate values
    assert format_bytes_human_readable(1024**1 + 512) == "1.500KB"
    assert format_bytes_human_readable(1024**2 + 512 * 1024) == "1.500MB"
    assert format_bytes_human_readable(1024**3 + 512 * 1024**2) == "1.500GB"

    # Test large values
    assert format_bytes_human_readable(2 * 1024**4) == "2.000TB"
    assert format_bytes_human_readable(1024**4 + 512 * 1024**3) == "1.500TB"
