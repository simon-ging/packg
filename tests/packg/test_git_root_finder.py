import pytest
from packg.iotools.git_root_finder import find_git_root
from pathlib import Path


def test_find_git_root(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    result = find_git_root(starting_dir=tmp_path)
    assert result == tmp_path
