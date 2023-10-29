import os
from pathlib import Path
from typing import List

import pytest

from packg.iotools.pathspec_matcher import PathSpecWithConversion
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
