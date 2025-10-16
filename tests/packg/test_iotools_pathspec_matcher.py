import os
from pathlib import Path
from typing import List

import pytest
from pathspec import PathSpec, Pattern

from packg.iotools.pathspec_matcher import (
    PathSpecArgs,
    PathSpecRepr,
    PathSpecWithConversion,
    apply_pathspecs,
    expand_pathspec_args,
    make_and_apply_pathspecs,
    make_pathspec,
    make_pathspecs,
    repr_pathspec,
)
from packg.testing.setup_tests import git_example_fixture, session_tmp_path

_ = git_example_fixture, session_tmp_path  # remove the unused false positive

FIX_FILE_README = "README.md"
FIX_FILE_SUBFILE = "subfolder/subfile.txt"
FIX_FILETREE_FLAT = [
    FIX_FILE_README,
    "LICENSE",
    "file.txt",
]

FIX_FILETREE = FIX_FILETREE_FLAT + [FIX_FILE_SUBFILE]


@pytest.fixture(scope="session")
def setup_file_tree(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("test_gitmatcher")
    for f in FIX_FILETREE:
        parts = Path(f).parts
        if len(parts) > 1:
            dir_to_create = tmp_path / "/".join(parts[:-1])
            os.makedirs(dir_to_create, exist_ok=True)
        (tmp_path / f).touch()
    yield tmp_path


@pytest.mark.parametrize(
    "spec_lines, expected_matches",
    [
        pytest.param([], [], id="empty"),
        pytest.param([""], [], id="blank"),
        pytest.param([FIX_FILE_README], [FIX_FILE_README], id="blank"),
        pytest.param([f"**/{FIX_FILE_README}"], [FIX_FILE_README], id="blank"),
        pytest.param([f"subfile.txt"], [FIX_FILE_SUBFILE], id="blank"),
        pytest.param([f"*/subfile.txt"], [FIX_FILE_SUBFILE], id="blank"),
        pytest.param([f"**/subfile.txt"], [FIX_FILE_SUBFILE], id="blank"),
        pytest.param([f"/subfile.txt"], [], id="blank"),
        pytest.param([f"*"], FIX_FILETREE, id="blank"),
    ],
)
def test_match_tree(spec_lines: List[str], expected_matches, setup_file_tree):
    base_path = setup_file_tree
    spec = PathSpecWithConversion(spec_lines, output_mode="str_posix")
    matches = list(spec.match_tree(base_path))
    print(f"GOT: {matches}")
    assert sorted(matches) == sorted(expected_matches)


@pytest.mark.parametrize(
    "spec_lines, expected_matches",
    [
        pytest.param([], [], id="empty"),
        pytest.param([""], [], id="blank"),
        pytest.param([FIX_FILE_README], [FIX_FILE_README], id="blank"),
        pytest.param([f"**/{FIX_FILE_README}"], [FIX_FILE_README], id="blank"),
        pytest.param([f"/subfile.txt"], [], id="blank"),
        pytest.param([f"*"], FIX_FILETREE_FLAT + ["subfolder"], id="blank"),
    ],
)
def test_match_files(spec_lines: List[str], expected_matches, setup_file_tree):
    base_path = setup_file_tree
    spec = PathSpecWithConversion(spec_lines, output_mode="str_posix")
    matches = list(spec.match_files(os.listdir(base_path)))
    assert sorted(matches) == sorted(expected_matches)


@pytest.mark.parametrize(
    "spec_lines, check_file, expected_bool",
    [
        pytest.param([], FIX_FILE_README, False, id="empty"),
        pytest.param([""], FIX_FILE_README, False, id="blank"),
        pytest.param([FIX_FILE_README], FIX_FILE_README, True, id="blank"),
        pytest.param([f"subfolder"], "subfolder", True, id="blank"),
        pytest.param([f"*"], "subfolder", True, id="blank"),
        pytest.param([f"*"], FIX_FILE_README, True, id="blank"),
    ],
)
def test_match_file(spec_lines: List[str], check_file: str, expected_bool, setup_file_tree):
    base_path = setup_file_tree
    spec = PathSpecWithConversion(spec_lines, output_mode="str_posix")
    assert spec.match_file(base_path / check_file) == expected_bool


def test_pathspec_repr():
    # Test PathSpecRepr string representation
    patterns = ["*.txt", "*.py"]
    spec = make_pathspecs(include_git=patterns)[0][0]  # Get the first PathSpec
    assert isinstance(spec, PathSpecRepr)
    assert "GitWildMatchPattern" in str(spec)
    assert "*.txt" in str(spec)
    assert "*.py" in str(spec)

    # Test pattern without 'pattern' attribute
    class DummyPattern(Pattern):
        def __init__(self):
            super().__init__(include=True)
            # Intentionally not setting pattern attribute

    spec = PathSpecRepr([DummyPattern()])
    assert "Unknown" in str(spec)
    assert "DummyPattern" in str(spec)


def test_regex_pathspec():
    # Test regex pathspec creation
    patterns = [r"test\.txt$", r"test\.py$"]  # More specific patterns
    spec = make_pathspec(patterns, regex_mode=True)

    # Test matching
    assert spec.match_file("test.txt")
    assert spec.match_file("test.py")
    assert not spec.match_file("test.log")
    assert not spec.match_file("mytest.txt")  # Should not match

    # Verify it's using regex patterns
    assert "RegexPattern" in repr_pathspec(spec)


def test_make_pathspecs(tmp_path):
    # Test making pathspecs with different patterns
    specs = make_pathspecs(
        include_git=["*.txt"],
        include_regex=[r"\.py$"],
        exclude_git=["*.log"],
        exclude_regex=[r"\.tmp$"],
    )
    assert len(specs) == 4

    # Test with gitignore file
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\n*.tmp")
    specs = make_pathspecs(exclude_gitignore_file=gitignore)
    assert len(specs) == 1


def test_apply_pathspecs(tmp_path):
    # Create test files
    files = [
        tmp_path / "test1.txt",
        tmp_path / "test2.py",
        tmp_path / "test3.log",
        tmp_path / "test4.tmp",
    ]
    for f in files:
        f.touch()

    # Test include patterns - convert Path objects to strings
    specs = make_pathspecs(include_git=["*.txt", "*.py"])
    matched = list(apply_pathspecs([f.as_posix() for f in files], specs))
    assert len(matched) == 2
    assert all(Path(f).suffix in [".txt", ".py"] for f in matched)

    # Test exclude patterns - convert Path objects to strings
    specs = make_pathspecs(exclude_git=["*.log", "*.tmp"])
    matched = list(apply_pathspecs([f.as_posix() for f in files], specs))
    assert len(matched) == 2
    assert all(Path(f).suffix in [".txt", ".py"] for f in matched)


def test_make_and_apply_pathspecs(tmp_path):
    # Create test files
    files = [
        tmp_path / "test1.txt",
        tmp_path / "test2.py",
        tmp_path / "test3.log",
        tmp_path / "test4.tmp",
    ]
    for f in files:
        f.touch()

    # Test with include and exclude patterns - convert Path objects to strings
    matched = list(
        make_and_apply_pathspecs(
            [f.as_posix() for f in files], include_git=["*.txt", "*.py"], exclude_git=["*.log", "*.tmp"]
        )
    )
    assert len(matched) == 2
    assert all(Path(f).suffix in [".txt", ".py"] for f in matched)


def test_pathspec_args():
    # Test PathSpecArgs creation
    args = PathSpecArgs(
        exclude_git=["*.log"],
        exclude_regex=[r"\.tmp$"],
        include_git=["*.txt"],
        include_regex=[r"\.py$"],
    )

    # Test expanding args
    expanded = expand_pathspec_args(args)
    assert expanded["exclude_git"] == ["*.log"]
    assert expanded["exclude_regex"] == [r"\.tmp$"]
    assert expanded["include_git"] == ["*.txt"]
    assert expanded["include_regex"] == [r"\.py$"]


def test_pathspec_with_conversion(tmp_path):
    # Create test files
    files = [
        tmp_path / "test1.txt",
        tmp_path / "test2.py",
        tmp_path / "test3.log",
    ]
    for f in files:
        f.touch()

    # Test with git patterns
    spec = PathSpecWithConversion(["*.txt", "*.py"])
    assert spec.match_file("test1.txt")
    assert spec.match_file("test2.py")
    assert not spec.match_file("test3.log")

    # Test match_files
    matched = list(spec.match_files(files))
    assert len(matched) == 2
    assert all(f.suffix in [".txt", ".py"] for f in matched)

    # Test match_tree
    matched = list(spec.match_tree(tmp_path))
    assert len(matched) == 2
    assert all(f.suffix in [".txt", ".py"] for f in matched)

    # Test different output modes
    spec_str = PathSpecWithConversion(["*.txt"], output_mode="str")
    spec_posix = PathSpecWithConversion(["*.txt"], output_mode="str_posix")

    matched_str = list(spec_str.match_files([files[0]]))
    matched_posix = list(spec_posix.match_files([files[0]]))

    assert isinstance(matched_str[0], str)
    assert isinstance(matched_posix[0], str)
    assert matched_posix[0] == str(files[0].as_posix())


def test_pathspec_with_dirs():
    specs = ["/subdir1"]
    rel_dirs = ["/subdir1", "/subdir2", "/subdir2/subdir1"]
    pathspecs = make_pathspecs(exclude_git=specs)
    print(f"Specs : {pathspecs}")
    remaining_dirs = list(apply_pathspecs(rel_dirs, pathspecs))
    remaining_dirs_str_sorted = sorted(remaining_dirs)
    assert remaining_dirs_str_sorted == ["/subdir2", "/subdir2/subdir1"]


def test_pathspec_with_dirs_no_leading_slash():
    # Note that without a trailing slash in the input directories, gitignore does not know they are
    # directories and does not exclude them.
    out = list(
        apply_pathspecs(
            ["/subdir1", "/subdir2"], make_pathspecs(exclude_git=["/subdir1/"])
        )
    )
    assert out == ["/subdir1", "/subdir2"]
