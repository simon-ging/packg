"""
Utilities to index and sort file trees.
"""
import itertools
import os
from operator import itemgetter
from pathlib import Path
from typing import Dict, Tuple, List

import natsort
from attr import define
from tqdm import tqdm

from packg.typext import PathType
from typedparser import NamedTupleMixin


def sort_file_paths_with_dirs_separated(
    file_paths: List[PathType], natsorted: bool = False, dirs_first: bool = True
) -> List[Path]:
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
        [(sort_index_dir, part) for part in path.parts[:-1]] + [(1, path.name)] for path in paths
    ]
    sort_fn = natsort.natsorted if natsorted else sorted
    sorted_tuples = sort_fn(zip(paths, key_paths), key=itemgetter(1))
    sorted_paths = [p[0] for p in sorted_tuples]
    return sorted_paths


@define
class FileProperties(NamedTupleMixin):
    size: int
    mtime: float


_total_counter = 0
_pbar: tqdm = None
_spinner = itertools.cycle("|/-\\")
_max_print = 40  # cut filenames when output is verbose
_count_every = 500  # how often to update the spinner


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
    global _total_counter, _pbar
    _total_counter = 0
    _pbar = tqdm(total=0, disable=not verbose, desc="Indexing files")
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
    _pbar.set_description(f"Indexed {len(file_dict)} files.")
    _pbar.clear()
    _pbar.close()
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
    global _total_counter
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
    if files is None:
        return entries

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
        if verbose and _total_counter % _count_every == 0:
            if show_file_if_verbose:
                file_out = rel_file
                if len(rel_file) > _max_print:
                    file_out = " ".join(
                        (rel_file[: _max_print // 2 - 3], "...", rel_file[-_max_print // 2 :])
                    )
            else:
                file_out = f"{stat.st_size / 1024 ** 2:13,.3f} MB"
            _pbar.set_description(f" {next(_spinner)} indexing {file_out}", refresh=False)
        _pbar.update(1)
        _total_counter += 1
    return entries
