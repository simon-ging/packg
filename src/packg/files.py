import os
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def set_working_directory(path: Path):
    """Change directory temporarily within in the context manager.
    """
    origin = Path(os.getcwd()).absolute()
    os.chdir(path)
    yield
    os.chdir(origin)
