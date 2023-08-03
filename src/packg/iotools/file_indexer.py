"""
Simple folder index
"""
import itertools
import os
from pathlib import Path
from typing import Dict, List, Tuple

from attr import define

from packg.typext import PathType
from typedparser import NamedTupleMixin

MAX_PRINT = 40  # cut filenames when output is verbose
SPINNER = itertools.cycle("|/-\\")
COUNT_EVERY = 500
total_counter = 0


@define
class FileProperties(NamedTupleMixin):
    size: int
    mtime: float


def make_index(
    base_root: PathType,
    recursive: bool = True,
    verbose: bool = True,
    reverse: bool = False,
    show_file_if_verbose: bool = False,
) -> Dict[str, FileProperties]:
    """Create file index dictionary of some path

    Args:
        base_root: input path
        recursive: recurse into subdirs
        verbose: verbosity (default True: print progress)
        reverse: output files in reverse order
        show_file_if_verbose: show file names in verbose mode (default False: only show file sizes)

    Returns:
        file dict {filename str : (file_size int, time_last_modified float) }
    """
    base_root = Path(base_root)
    global total_counter
    total_counter = 0
    file_list = _recursive_index(
        base_root,
        base_root,
        0,
        recursive=recursive,
        verbose=verbose,
        reverse=reverse,
        show_file_if_verbose=show_file_if_verbose,
    )
    file_dict = {}
    for filename, size, modtime in file_list:
        file_dict[filename] = FileProperties(size, modtime)
    assert len(file_dict) == len(file_list)
    if verbose:
        print()
        print(f"done indexing {len(file_dict)} files. ")
    return file_dict


def _recursive_index(
    root: Path,
    base_root: Path,
    depth: int,
    recursive: bool = True,
    verbose: bool = True,
    reverse: bool = False,
    show_file_if_verbose: bool = False,
) -> List[Tuple[str, int, float]]:
    """Recursive helper function for make_index

    Args:
        root: current root
        base_root: total root where the indexing started
        depth: current depth

    Returns:
        list of tuples (filename str, file_size_bytes int, time_last_modified float)
    """
    global total_counter
    entries = []
    base_root_length = len(base_root.parts)
    # get paths and files
    dirs, files = None, None
    for _, dirs, files in os.walk(root):
        break

    def sorter(input_list):
        if input_list is None:
            return None
        if reverse:
            return reversed(sorted(input_list))
        return sorted(input_list)

    dirs = sorter(dirs)
    files = sorter(files)
    if dirs is not None and recursive:
        for d in dirs:
            root_new = root / d
            entries += _recursive_index(
                root_new,
                base_root,
                depth + 1,
                recursive=recursive,
                verbose=verbose,
                reverse=reverse,
                show_file_if_verbose=show_file_if_verbose,
            )
    if files is not None:
        for f in files:
            # build file name relative to base_root, unix path style
            full_file = root / f
            rel_parts = full_file.parts[base_root_length:]

            # save it in unix notation (/)
            rel_file = "/".join(rel_parts)

            # get size and mod time
            stat = full_file.stat()
            entries.append((rel_file, int(stat.st_size), float(stat.st_mtime)))

            # logging
            if verbose and total_counter % COUNT_EVERY == 0:
                if show_file_if_verbose:
                    file_out = rel_file
                    if len(rel_file) > MAX_PRINT:
                        file_out = " ".join(
                            (rel_file[: MAX_PRINT // 2 - 3], "...", rel_file[-MAX_PRINT // 2 :])
                        )
                else:
                    file_out = f"{stat.st_size / 1024 ** 2:13,.3f} MB"
                print(f" {next(SPINNER)} {total_counter} indexing {file_out}", end="\r")
            total_counter += 1
    return entries
