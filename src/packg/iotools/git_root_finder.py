import os
import sys
from pathlib import Path
from typing import Optional

from packg.typext import PathType


def navigate_to_git_root(starting_dir: Optional[PathType] = None, verbose=False):
    target_dir = find_git_root(starting_dir, verbose)
    os.chdir(target_dir)


def find_git_root(starting_dir: Optional[PathType] = None, verbose=False):
    if starting_dir is None:
        starting_dir = os.getcwd()
    if verbose:
        print(f"Starting dir: {starting_dir}")
    current_dir = Path(starting_dir)
    found = False
    for _ in range(128):
        if (current_dir / ".git").is_dir():
            found = True
            break
        if current_dir == current_dir.parent:
            break
        current_dir = current_dir.parent
    if not found:
        raise RuntimeError("Could not find repo root.")
    if verbose:
        print(f"Final dir:    {current_dir}")
    return current_dir


def add_git_root_to_path(starting_dir: Optional[PathType] = None, verbose=False):
    target_dir = find_git_root(starting_dir, verbose).as_posix()
    if target_dir != starting_dir and target_dir not in sys.path:
        sys.path.insert(0, target_dir)
        if verbose:
            print(f"Added to path: {target_dir}")
