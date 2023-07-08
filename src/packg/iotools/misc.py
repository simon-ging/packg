import os
from contextlib import contextmanager
from operator import itemgetter
from pathlib import Path
from typing import Union, Iterable, TextIO, List

import natsort
from packg.typext import PathOrIO, PathTypeCls, PathType


@contextmanager
def set_working_directory(path: Path):
    """Change directory temporarily within in the context manager.
    """
    origin = Path(os.getcwd()).absolute()
    os.chdir(path)
    yield
    os.chdir(origin)


@contextmanager
def open_file_or_io(file_or_io: PathOrIO, mode="r", encoding="utf-8", create_parent=False, ):
    should_close = False
    if isinstance(file_or_io, (str, PathTypeCls)):
        file_or_io = Path(file_or_io)
        if create_parent:
            os.makedirs(file_or_io.parent, exist_ok=True)
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
    with open_file_or_io(file_or_io, mode="rb") as fh:
        while True:
            data = fh.read(chunk_size)
            if len(data) == 0:
                break
            yield data


def yield_nonempty_stripped_lines(lines_obj: Union[PathOrIO, Iterable[str]]) -> Iterable[str]:
    """
    Read lines from input, strip whitespaces, skip empty lines, yield lines.

    Args:
        lines_obj: Can be any of:
            - iterable of str (list, opened file)
            - filepath str or Path

    Returns:
        Generator of stripped lines

    Examples:
        >>> for li in yield_nonempty_stripped_lines(["  a  ", "  ", "  b  "]): print(li, end=",")
        a,b,
    """
    if isinstance(lines_obj, str):
        lines_obj = lines_obj.splitlines()
    with open_file_or_io(lines_obj) as fh:
        for line in fh:
            line = line.strip()
            if line == "":
                continue
            yield line


def sort_file_paths_with_dirs_separated(
        file_paths: List[PathType], natsorted: bool = False,
        dirs_first: bool = True) -> List[Path]:
    """
    Sort a list of file paths, separating files inside subdirectories from files in the root.

    Only works for file paths (not directory paths) - input "dir/" will be treated like "dir"
    since in pathlib, Path("dir/") and Path("dir") are the same thing.

    Args:
        file_paths:
        natsorted: natural sort (image1, image2, image10) instead of (image1, image10, image2)
        dirs_first: if True, sort directories before files, otherwise sort files before dirs

    Returns:
        sorted list of paths
    """
    paths = [Path(p) for p in file_paths]
    sort_index_dir = 0 if dirs_first else 2
    # split path into its parts, then create a list of (sort_index, part) tuple for the path
    key_paths = [
        [(sort_index_dir, part) for part in path.parts[:-1]] + [(1, path.name)]
        for path in paths
    ]
    sort_fn = natsort.natsorted if natsorted else sorted
    sorted_tuples = sort_fn(zip(paths, key_paths), key=itemgetter(1))
    sorted_paths = [p[0] for p in sorted_tuples]
    return sorted_paths
