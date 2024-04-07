"""
Utilities to index and sort file trees.
"""

from __future__ import annotations

import itertools
import os
import re
from operator import itemgetter
from pathlib import Path
from typing import Iterator, Union, Optional

import natsort
from attr import define
from tqdm import tqdm

from packg.iotools.pathspec_matcher import (
    PathSpecArgs,
    make_pathspecs,
    expand_pathspec_args,
    SPECLISTTYPE,
    apply_pathspecs,
)
from packg.typext import PathType
from typedparser import NamedTupleMixin


def regex_glob(
    base_path: PathType,
    regex_pattern: Union[re.Pattern, str],
    glob_pattern: str = "**/*",
    match_filename_only: bool = False,
    match_inverse: bool = False,
    ignore_directories: bool = False,
    return_relative_paths: bool = False,
    return_as_posix_str: bool = False,
) -> Iterator[Union[PathType, str]]:
    """Glob with regex filter

    Args:
        base_path: base path
        regex_pattern: regex pattern to filter
        glob_pattern: glob pattern to filter, potentially increase performance by pre-filtering
        match_filename_only: match only the filename, not the full path
        match_inverse: return files that do not match the regex
        ignore_directories: ignore directories in output results
        return_relative_paths: return relative paths instead of absolute paths
        return_as_posix_str: return as posix string instead of Path object

    Returns:
        list of paths
    """
    # print(f"Got pattern {regex_pattern}")
    if isinstance(regex_pattern, str):
        # print(f"Compiling {regex_pattern}")
        regex_pattern = re.compile(regex_pattern)
        # print(f"Got {regex_pattern}")
    glob_results = list(Path(base_path).glob(glob_pattern))
    # print("got", len(glob_results),"results for", base_path, glob_pattern,":\n", glob_results)
    for pth in glob_results:
        if match_filename_only:
            str_to_match = pth.name
        else:
            str_to_match = pth.as_posix()
        re_matches_bool = bool(regex_pattern.search(str_to_match))
        # print("match", re_matches_bool, "for", str_to_match, "with", regex_pattern)
        if match_inverse:
            re_matches_bool = not re_matches_bool
        if re_matches_bool:
            if ignore_directories and pth.is_dir():
                continue
            if return_relative_paths:
                pth = pth.relative_to(base_path)
            if return_as_posix_str:
                pth = pth.as_posix()
            yield pth


def sort_file_paths_with_dirs_separated(
    file_paths: list[PathType], natsorted: bool = False, dirs_first: bool = True
) -> list[Path]:
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


_total_counter, _ignored_dirs_counter, _ignored_files_counter = 0, 0, 0
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
    pathspec_args: Optional[PathSpecArgs] = None,
    follow_symlinks: bool = False,
) -> dict[str, FileProperties]:
    """Create file index dictionary of some path

    Args:
        base_root: input path
        recursive: recurse into subdirs
        verbose: verbosity (default True: print progress)
        reverse: output files in reverse order
        show_file_if_verbose: show file names in verbose mode (default False: only show file sizes)
        pathspec_args: optional pathspec arguments to filter files
        follow_symlinks: follow symlinks (default False) both by recursing into symlinked dirs and
            by indexing symlinked files.

    Returns:
        file dict {filename str : (file_size int, time_last_modified float) }
    """
    base_root = Path(base_root).resolve().absolute()
    global _total_counter, _pbar, _ignored_dirs_counter, _ignored_files_counter
    _total_counter = 0
    _pbar = tqdm(total=0, disable=not verbose, desc="Indexing files")
    specs = []
    if pathspec_args is not None:
        specs = make_pathspecs(**expand_pathspec_args(pathspec_args))
    file_list = _recursive_index(
        base_root,
        base_root,
        0,
        recursive=recursive,
        verbose=verbose,
        reverse=reverse,
        show_file_if_verbose=show_file_if_verbose,
        specs=specs,
        follow_symlinks=follow_symlinks,
    )
    file_dict = {}
    for filename, size, modtime in file_list:
        file_dict[filename] = FileProperties(size, modtime)
    assert len(file_dict) == len(file_list)
    _pbar.set_description(
        f"Indexed {len(file_dict)} files. Ignored {_ignored_dirs_counter} dirs and "
        f"{_ignored_files_counter} files."
    )
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
    specs: Optional[SPECLISTTYPE, None] = None,
    follow_symlinks: bool = False,
) -> list[tuple[str, int, float]]:
    """Recursive helper function for make_index

    Args:
        root: current root
        base_root: total root where the indexing started
        depth: current depth

    Returns:
        list of tuples (filename str, file_size_bytes int, time_last_modified float)
    """
    if specs is None:
        specs = []
    global _total_counter, _ignored_dirs_counter, _ignored_files_counter
    entries = []
    dirs, files = None, None
    for _, dirs, files in os.walk(root, followlinks=follow_symlinks):
        # probably the followlinks doesn't do anything here since we do not recurse with os.walk
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
        abs_dirs = []
        for d in dirs:
            abs_dir = (root / d).absolute()
            if not abs_dir.is_dir():  # protect against things like mounts, only index real dirs.
                continue
            if abs_dir.is_symlink():
                if not follow_symlinks:
                    continue
                else:
                    # reading the link will raise an error if the link is broken.
                    abs_dir.readlink()
            abs_dirs.append(abs_dir)
        if not follow_symlinks:
            abs_dirs = [d for d in abs_dirs if not d.is_symlink()]
        if len(specs) > 0:
            # convert to relative directories and filter with the pathspecs, then convert back
            rel_dirs = [d.relative_to(base_root) for d in abs_dirs]
            n_before = len(rel_dirs)
            rel_dirs = list(apply_pathspecs(rel_dirs, specs))
            _ignored_dirs_counter += n_before - len(rel_dirs)
            abs_dirs = [base_root / d for d in rel_dirs]
        for root_new in abs_dirs:
            entries += _recursive_index(
                root_new,
                base_root,
                depth + 1,
                recursive=recursive,
                verbose=verbose,
                reverse=reverse,
                show_file_if_verbose=show_file_if_verbose,
                specs=specs,
                follow_symlinks=follow_symlinks,
            )
    if files is None:
        return entries

    abs_files = []
    for f in files:
        abs_file = (root / f).absolute()
        if abs_file.is_symlink() and follow_symlinks:
            # pathlib silently ignores recursive symlinks. the way to detect the error is because
            # it is not a directory anymore, but following it will lead to a directory.
            linked_file = abs_file.readlink()
            if linked_file.is_dir() and not abs_file.is_dir():
                raise RuntimeError(f"Broken symlink, potentially recursive: {abs_file} -> {linked_file}")
        if not abs_file.is_file():
            # .is_file() safeguards against stuff like /dev/zero which returns .is_char_device()
            continue
        if abs_file.is_symlink() and not follow_symlinks:
            continue
        abs_files.append(abs_file)
    rel_files = [f.relative_to(base_root) for f in abs_files]
    if len(specs) > 0:
        # filter with pathspecs on relative file level
        n_before = len(rel_files)
        rel_files = list(apply_pathspecs(rel_files, specs))
        _ignored_files_counter += n_before - len(rel_files)
        abs_files = [base_root / ff for ff in rel_files]

    for abs_file, rel_file in zip(abs_files, rel_files):
        rel_file_str = rel_file.as_posix()

        # get size and mod time
        stat = abs_file.stat()
        entries.append((rel_file_str, int(stat.st_size), float(stat.st_mtime)))

        # logging
        if verbose and _total_counter % _count_every == 0:
            if show_file_if_verbose:
                file_out = rel_file_str
                if len(rel_file_str) > _max_print:
                    half = _max_print // 2
                    file_out = " ".join((rel_file_str[: half - 3], "...", rel_file_str[half:]))
            else:
                file_out = f"{stat.st_size / 1024 ** 2:13,.3f} MB"
            _pbar.set_description(f" {next(_spinner)} indexing {file_out}", refresh=False)
        _pbar.update(1)
        _total_counter += 1
    return entries
