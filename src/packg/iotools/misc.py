import os
from contextlib import contextmanager
from pathlib import Path

from packg.typext import PathType


@contextmanager
def set_working_directory(path: Path):
    """Change directory temporarily within in the context manager."""
    origin = Path(os.getcwd()).absolute()
    os.chdir(path)
    yield
    os.chdir(origin)


def get_file_size(input_file: PathType, scale: int = 0) -> float:
    """
    Args:
        input_file:
        scale: 0=B (default), 1=KB, 2=MB, 3=GB, etc.

    Returns:
        File size in specified scale
    """
    return Path(input_file).stat().st_size / 1024**scale


def get_file_size_in_mb(input_file: PathType) -> float:
    return get_file_size(input_file, scale=2)


def format_b_in_mb(size_b: int) -> str:
    return f"{size_b / 1024 ** 2:.3f}MB"


def format_b_in_gb(size_b: int) -> str:
    return f"{size_b / 1024 ** 3:.3f}GB"


def format_bytes_human_readable(size_b: int) -> str:
    scales = ["B", "KB", "MB", "GB", "TB"]
    for scale, unit in enumerate(scales):
        if size_b < 1024 ** (scale + 1) or scale == len(scales) - 1:
            return f"{size_b / 1024 ** scale:.3f}{unit}"
    raise RuntimeError("Should not reach here")
