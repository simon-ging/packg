"""
Utilities to read content of a single file.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Union

from packg.typext import PathOrIO, PathType, PathTypeCls


@contextmanager
def open_file_or_io(
    file_or_io: PathOrIO,
    mode="r",
    encoding="utf-8",
    create_parent=False,
):
    should_close = False
    if isinstance(file_or_io, PathTypeCls):
        file_or_io = Path(file_or_io)
        if create_parent:
            os.makedirs(file_or_io.parent, exist_ok=True)
        if "b" in mode:
            encoding = None
        fh = file_or_io.open(mode, encoding=encoding)
        should_close = True
    else:
        fh = file_or_io
    yield fh
    if should_close:
        fh.close()


def read_text_from_file_or_io(file_or_io: PathOrIO, encoding: str = "utf-8") -> str:
    """
    Args:
        file_or_io: file name or open file-like object
        encoding: encoding to use for reading

    Returns:
        text content
    """
    if isinstance(file_or_io, PathTypeCls):
        return Path(file_or_io).read_text(encoding=encoding)
    return file_or_io.read()


def read_bytes_from_file_or_io(file_or_io: PathOrIO) -> bytes:
    """

    Args:
        file_or_io: file name or open file-like object

    Returns:
        bytes content
    """
    if isinstance(file_or_io, PathTypeCls):
        return Path(file_or_io).read_bytes()
    return file_or_io.read()


def yield_chunked_bytes(file_or_io: PathOrIO, chunk_size=1024 * 1024) -> Iterable[bytes]:
    """

    Args:
        file_or_io: file name or open file-like object
        chunk_size: chunk size in bytes, default 1MB

    Returns:
        bytes content
    """
    with open_file_or_io(file_or_io, mode="rb") as fh:  # noqa, pylint: disable=W0135
        while True:
            data = fh.read(chunk_size)  # noqa
            if len(data) == 0:
                break
            yield data


def yield_lines_from_object(
    lines_obj: Union[str, Iterable[str]], strip: bool = True, skip_empty: bool = True
) -> Iterable[str]:
    """
    Read lines from input, strip whitespaces, skip empty lines, yield lines.

    Args:
        lines_obj: Either str or iterable of str (list, opened file)
        strip: strip whitespace from lines
        skip_empty: skip empty lines

    Returns:
        Generator of stripped lines

    Examples:
        >>> for li in yield_lines_from_object(["  a  ", "  ", "  b  "]): print(li, end=",")
        a,b,
    """
    if isinstance(lines_obj, str):
        lines_obj = lines_obj.splitlines()
    for line in lines_obj:
        if strip:
            line = line.strip()
        if skip_empty:
            if line == "":
                continue
        yield line


def yield_lines_from_file(
    file: PathType, strip: bool = True, skip_empty: bool = True, encoding: str = "utf-8"
) -> Iterable[str]:
    """
    Read lines from input, strip whitespaces, skip empty lines, yield lines.

    Args:
        file: file path as string
        strip: strip whitespace from lines
        skip_empty: skip empty lines
        encoding: encoding to use for reading

    Returns:
        Generator of stripped lines
    """
    with Path(file).open(encoding=encoding) as fh:
        while True:
            next_line = fh.readline()
            if len(next_line) == 0:
                # empty lines will have at least a newline character
                # so this is only true if EOF is reached.
                break
            if strip:
                next_line = next_line.strip()
            if skip_empty:
                if strip and next_line == "":
                    continue
                if not strip and next_line.strip("\r\n") == "":
                    continue
            yield next_line
