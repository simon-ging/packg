from pathlib import Path
from typing import Iterator

import pytest

from packg.iotools.file_indexer import make_index
from packg.iotools.pathspec_matcher import PathSpecArgs


def count_files_and_dirs(base_path: Path) -> tuple[int, int]:
    """Count total files and directories in a path recursively."""
    file_count = 0
    dir_count = 0
    for item in base_path.rglob("*"):
        if item.is_file():
            file_count += 1
        elif item.is_dir():
            dir_count += 1
    return file_count, dir_count


def print_test_status(test_name: str, base_path: Path, result: dict, status: dict):
    """Print comprehensive status for a test."""
    input_files, input_dirs = count_files_and_dirs(base_path)
    output_files = len(result)
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")
    print(f"Input:  {input_files} files, {input_dirs} directories")
    print(f"Output: {output_files} files")
    for k, v in status.items():
        print(f"  - {k}: {v}")
    print(f"{'='*60}\n")


@pytest.fixture
def temp_file_structure(tmp_path: Path) -> Iterator[Path]:
    """
    Create a temporary folder structure for testing:

    file1.txt
    file2.py
    file3.md
    subdir1
    subdir1/file4.txt
    subdir1/file5.py
    subdir1/nested
    subdir1/nested/file8.txt
    subdir1/nested/subdir_nested
    subdir1/nested/subdir_nested/file10.py
    subdir1/nested/subdir_nested/file9.txt
    subdir2
    subdir2/file6.md
    subdir2/file7.txt
    subdir2/subdir1
    subdir2/subdir1/file11.txt
    subdir2/subdir1/file12.py
    """
    # Create files in root
    (tmp_path / "file1.txt").write_text("content1")
    (tmp_path / "file2.py").write_text("content2")
    (tmp_path / "file3.md").write_text("content3")

    # Create subdirectory 1 with files
    subdir1 = tmp_path / "subdir1"
    subdir1.mkdir()
    (subdir1 / "file4.txt").write_text("content4")
    (subdir1 / "file5.py").write_text("content5")

    # Create nested subdirectory with subdir_nested (not subdir1)
    nested = subdir1 / "nested"
    nested.mkdir()
    (nested / "file8.txt").write_text("content8")

    subdir_nested = nested / "subdir_nested"
    subdir_nested.mkdir()
    (subdir_nested / "file9.txt").write_text("content9")
    (subdir_nested / "file10.py").write_text("content10")

    # Create subdirectory 2 with files
    subdir2 = tmp_path / "subdir2"
    subdir2.mkdir()
    (subdir2 / "file6.md").write_text("content6")
    (subdir2 / "file7.txt").write_text("content7")

    # Create subdir1 as subfolder of subdir2
    subdir2_subdir1 = subdir2 / "subdir1"
    subdir2_subdir1.mkdir()
    (subdir2_subdir1 / "file11.txt").write_text("content11")
    (subdir2_subdir1 / "file12.py").write_text("content12")

    yield tmp_path

    # Cleanup is automatic with tmp_path fixture


def test_make_index_basic(temp_file_structure: Path):
    """Test make_index without pathspec filtering."""
    result, status = make_index(temp_file_structure, verbose=False, return_status=True)
    print_test_status("test_make_index_basic", temp_file_structure, result, status)

    # Check that all 12 files are indexed
    assert len(result) == 12

    # Check that expected files are present
    expected_files = [
        "file1.txt",
        "file2.py",
        "file3.md",
        "subdir1/file4.txt",
        "subdir1/file5.py",
        "subdir1/nested/file8.txt",
        "subdir1/nested/subdir_nested/file9.txt",
        "subdir1/nested/subdir_nested/file10.py",
        "subdir2/file6.md",
        "subdir2/file7.txt",
        "subdir2/subdir1/file11.txt",
        "subdir2/subdir1/file12.py",
    ]

    for expected_file in expected_files:
        assert expected_file in result
        # Check that file properties are recorded
        assert result[expected_file].size > 0
        assert result[expected_file].mtime > 0


def test_make_index_non_recursive(temp_file_structure: Path):
    """Test make_index without recursion."""
    result, status = make_index(temp_file_structure, recursive=False, verbose=False, return_status=True)
    print_test_status("test_make_index_non_recursive", temp_file_structure, result, status)

    # Should only have 3 files from root directory
    assert len(result) == 3

    # Check that only root files are present
    assert "file1.txt" in result
    assert "file2.py" in result
    assert "file3.md" in result

    # Check that subdirectory files are excluded
    assert "subdir1/file4.txt" not in result
    assert "subdir1/file5.py" not in result
    assert "subdir2/file6.md" not in result
    assert "subdir2/file7.txt" not in result

def test_make_index_with_pathspec_exclude_git(temp_file_structure: Path):
    """Test make_index with pathspec args to exclude files using git patterns."""
    pathspec_args = PathSpecArgs(
        exclude_git=["*.py"],  # Exclude all Python files
    )

    result, status = make_index(temp_file_structure, verbose=False, pathspec_args=pathspec_args, return_status=True)
    print_test_status("test_make_index_with_pathspec_exclude_git", temp_file_structure, result, status)

    # Should have 8 files (excluded 4 .py files)
    assert len(result) == 8

    # Check that .py files are excluded
    assert "file2.py" not in result
    assert "subdir1/file5.py" not in result
    assert "subdir1/nested/subdir_nested/file10.py" not in result
    assert "subdir2/subdir1/file12.py" not in result

    # Check that other files are present
    assert "file1.txt" in result
    assert "file3.md" in result
    assert "subdir1/file4.txt" in result
    assert "subdir1/nested/file8.txt" in result
    assert "subdir1/nested/subdir_nested/file9.txt" in result
    assert "subdir2/file6.md" in result
    assert "subdir2/file7.txt" in result
    assert "subdir2/subdir1/file11.txt" in result


def test_make_index_with_pathspec_exclude_directory_anywhere(temp_file_structure: Path):
    """Test make_index with pathspec args to exclude 'subdir1/' anywhere in the tree.

    This should exclude both root-level subdir1/ and subdir2/subdir1/.
    """
    pathspec_args = PathSpecArgs(
        exclude_git=["subdir1/"],  # Exclude subdir1 anywhere in the tree
    )

    result, status = make_index(temp_file_structure, verbose=False, pathspec_args=pathspec_args, return_status=True)
    print_test_status("test_make_index_with_pathspec_exclude_directory_anywhere", temp_file_structure, result, status)

    # Should have 5 files (excluded all files from both subdir1 directories)
    assert len(result) == 5

    # Check that both subdir1 directories are excluded (and all their contents)
    assert "subdir1/file4.txt" not in result
    assert "subdir1/file5.py" not in result
    assert "subdir1/nested/file8.txt" not in result
    assert "subdir1/nested/subdir_nested/file9.txt" not in result
    assert "subdir1/nested/subdir_nested/file10.py" not in result
    assert "subdir2/subdir1/file11.txt" not in result
    assert "subdir2/subdir1/file12.py" not in result

    # Check that other files are present
    assert "file1.txt" in result
    assert "file2.py" in result
    assert "file3.md" in result
    assert "subdir2/file6.md" in result
    assert "subdir2/file7.txt" in result


def test_make_index_with_pathspec_exclude_directory_root_only(temp_file_structure: Path):
    """Test make_index with pathspec args to exclude '/subdir1/' only at root level.

    The leading slash '/' means to match only at root level. This should exclude the
    root-level subdir1/ and all its contents, but NOT exclude subdir2/subdir1/.
    """
    print()
    print(f"Temporary test directory: {temp_file_structure}")
    print('\n'.join(sorted(p.relative_to(temp_file_structure).as_posix() for p in temp_file_structure.rglob('*'))))
    pathspec_args = PathSpecArgs(
        exclude_git=["/subdir1/"],  # Exclude subdir1 only at root (not subdir2/subdir1/)
    )

    result, status = make_index(
        temp_file_structure, verbose=False, pathspec_args=pathspec_args, return_status=True
    )
    print_test_status(
        "test_make_index_with_pathspec_exclude_directory_root_only",
        temp_file_structure,
        result,
        status,
    )
    assert len(status["ignored_dirs"]) == 1
    assert status["ignored_dirs"] == ["/subdir1/"]
    # the ignored files must never be iterated over so they don't show up in the counter
    # this is alot more efficient than finding all files and then filtering them out
    assert len(status["ignored_files"]) == 0

    # Should have 7 files (excluded root subdir1 but kept subdir2/subdir1)
    assert len(result) == 7

    # Check that root subdir1 and all its contents are excluded
    assert "subdir1/file4.txt" not in result
    assert "subdir1/file5.py" not in result
    assert "subdir1/nested/file8.txt" not in result
    assert "subdir1/nested/subdir_nested/file9.txt" not in result
    assert "subdir1/nested/subdir_nested/file10.py" not in result

    # Check that subdir2/subdir1 is NOT excluded
    assert "subdir2/subdir1/file11.txt" in result
    assert "subdir2/subdir1/file12.py" in result

    # Check that other files are present
    assert "file1.txt" in result
    assert "file2.py" in result
    assert "file3.md" in result
    assert "subdir2/file6.md" in result
    assert "subdir2/file7.txt" in result
