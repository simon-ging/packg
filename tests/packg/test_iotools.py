import io
from pathlib import Path

import pytest

from packg.iotools import (
    read_text_from_file_or_io,
    read_bytes_from_file_or_io,
    yield_lines_from_file,
    yield_lines_from_object,
    find_git_root,
    sort_file_paths_with_dirs_separated,
)

_ref = ["a", "b", "c"]
_inp_str = "\na\n    b\n    c\n\n"


def test_read_text_from_file_or_io(tmp_path):
    assert read_text_from_file_or_io(io.StringIO(_inp_str)) == _inp_str
    file = tmp_path / "example.txt"
    file.write_text(_inp_str, encoding="utf-8")
    assert read_text_from_file_or_io(file) == _inp_str


def test_read_bytes_from_file_or_io(tmp_path):
    inp_str_bytes = bytes(_inp_str, encoding="utf-8")
    assert read_bytes_from_file_or_io(io.BytesIO(inp_str_bytes)) == inp_str_bytes
    file = tmp_path / "example.txt"
    file.write_bytes(inp_str_bytes)
    assert read_bytes_from_file_or_io(file) == inp_str_bytes


@pytest.mark.parametrize(
    "inp, ref",
    [
        (_inp_str.splitlines(), _ref),
        (io.StringIO(_inp_str), _ref),
        (
            [" a  ", "  ", "  b  ", "c", "  "],
            _ref,
        ),
    ],
    ids=["str", "io", "list"],
)
def test_yield_nonempty_stripped_lines(inp, ref):
    cand = list(yield_lines_from_object(inp))
    assert cand == ref


def test_yield_nonempty_stripped_lines_from_file(tmp_path):
    file = tmp_path / "example.txt"
    file.write_text(_inp_str, encoding="utf-8")
    cand = list(yield_lines_from_file(file))
    assert cand == _ref


_inp_paths = ["foo/bar", "foo/baz", "zfoo/bar", "foo1", "foo10", "foo2"]


@pytest.mark.parametrize(
    "inp, natsorted, dirs_first, ref",
    [
        (
            _inp_paths,
            False,
            False,
            ["foo1", "foo10", "foo2", "foo/bar", "foo/baz", "zfoo/bar"],
        ),
        (
            _inp_paths,
            True,
            False,
            ["foo1", "foo2", "foo10", "foo/bar", "foo/baz", "zfoo/bar"],
        ),
        (
            _inp_paths,
            False,
            True,
            ["foo/bar", "foo/baz", "zfoo/bar", "foo1", "foo10", "foo2"],
        ),
        (
            _inp_paths,
            True,
            True,
            ["foo/bar", "foo/baz", "zfoo/bar", "foo1", "foo2", "foo10"],
        ),
    ],
    ids=["default", "natsorted", "dirs_first", "natsorted_dirs_first"],
)
def test_sort_paths_with_dirs_separated(inp, natsorted, dirs_first, ref):
    cand = sort_file_paths_with_dirs_separated(inp, natsorted=natsorted, dirs_first=dirs_first)
    cand_str = [p.as_posix() for p in cand]
    print(f"natsorted={natsorted}, dirs_first={dirs_first}")
    print(f"ref={ref}")
    print(f"cand={cand_str}")
    print()
    assert cand_str == ref


def test_find_git_root():
    assert Path(find_git_root()).is_dir()
