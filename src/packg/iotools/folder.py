from __future__ import annotations

import os
from functools import partial
from pathlib import Path
from typing import Optional

from attr import define
from attrs import field
from loguru import logger

from packg import format_exception
from packg.iotools import format_b_in_mb
from packg.iotools.misc import format_b_in_gb


@define
class Folder:
    """
    Recursive folder class to get and print sizes of all files and folders in a directory.

    Usage:
        root = Folder("/path/to/folder")
        root.populate(recursive=True)
        print(root.total_size)
    """

    full_path: Path = field()
    running_total_size: int = field(default=0, repr=False)
    last_total_size: int = field(default=0, repr=False)

    # Initialize other fields with default factory
    files_and_stat: dict[str, os.stat_result] = field(factory=dict, init=False, repr=False)
    own_stat: Optional[os.stat_result] = field(default=None, init=False, repr=False)
    dir_refs: dict[str, Folder] = field(factory=dict, init=False, repr=False)
    files_size: int = field(default=0, init=False)
    dirs_size: int = field(default=0, init=False)
    total_size: int = field(default=0, init=False)
    populated: bool = field(default=False, init=False)

    def __attrs_post_init__(self):
        self.full_path = Path(self.full_path)

    def populate(self, recursive: bool = True, level: int = 0):
        if self.populated:
            return

        self.own_stat = self.full_path.stat()
        if (self.running_total_size - self.last_total_size) > 1024**3:
            logger.info(f"... {format_b_in_gb(self.running_total_size):10s} at {self.full_path}")
            self.last_total_size = self.running_total_size

        start_path = Path(self.full_path)
        indent = "    " * level
        logger.debug(f"{indent}Finding all files in {start_path}")
        dirs = []
        files_size = 0
        for file in sorted(os.listdir(start_path)):
            full_file = start_path / file
            try:
                if full_file.is_symlink():
                    logger.debug(f"{indent}SKIP {full_file} (symlink)")
                    continue
                if full_file.is_dir():
                    dirs.append(file)
                    continue
                if full_file.is_file():
                    self.files_and_stat[file] = full_file.stat()
                    continue
            except OSError as e:
                logger.warning(f"{indent}SKIP {full_file} ({format_exception(e)})")
            logger.debug(f"{indent}SKIP {full_file} (neither file nor dir?)")
        logger.debug(f"File size: {files_size}")
        self.files_size = sum(st.st_size for st in self.files_and_stat.values())
        self.running_total_size += self.files_size

        if recursive:
            for i, dr in enumerate(dirs):
                if level == 0:
                    logger.info(f"Folder {i:3d}/{len(dirs)}: {dr}")
                logger.debug(f"Recurse into: {dr}")

                full_dr = start_path / dr
                folder = Folder(
                    full_dr,
                    running_total_size=self.running_total_size,
                    last_total_size=self.last_total_size,
                )
                folder.populate(recursive=recursive, level=level + 1)
                self.running_total_size += folder.total_size
                self.last_total_size = folder.last_total_size

                self.dir_refs[dr] = folder

        self.dirs_size = sum(v.total_size for v in self.dir_refs.values())
        self.total_size = self.files_size + self.dirs_size
        logger.debug(f"{indent}Got total size {format_b_in_mb(self.total_size)} for {start_path}")
        self.populated = True

    def get_dir_index(self, base_dir="", level: int = 0, max_level: int = -1):
        """
        Returns:
            list of tuples [(dir_name, total_size )]
        """
        self.populate()
        dir_index = []
        for dir_name, dir_ref in self.dir_refs.items():
            dir_index.append((f"{base_dir}{dir_name}", dir_ref.total_size))
            if level < max_level or max_level < 0:
                dir_index.extend(
                    dir_ref.get_dir_index(
                        base_dir=f"{base_dir}{dir_name}/", level=level + 1, max_level=max_level
                    )
                )
        return dir_index


def get_subfolder_data(
    root: Folder,
    level: int = 0,
    max_level: int = -1,
    min_size_mb: float = 100,
    full_path_to_here="",
) -> list[tuple[str, str, int, float]]:
    """
    Create tabular info about subfolders. This should not be included in the Folder class,
    since it recursively calls different instances of the Folder class.

    Args:
        root: root folder to start from
        level: current recursion level
        max_level: maximum recursion level
        min_size_mb: minimum size in MB to include in the output
        full_path_to_here: path to the current folder

    Returns:
        list of tuples [(path, type, size, mtime)] for each file or folder

    """
    _recursive_call = partial(
        get_subfolder_data,
        level=level + 1,
        max_level=max_level,
        min_size_mb=min_size_mb,
    )
    output = []
    min_size_b = min_size_mb * 1024**2
    if max_level == 0:
        return
    size_b_other_files = 0
    for file, file_stat in root.files_and_stat.items():
        file_size = file_stat.st_size
        if file_size >= min_size_b:
            output.append(
                (
                    f"{full_path_to_here}{file}",
                    "f",
                    file_size,
                    file_stat.st_mtime,
                )
            )
            continue
        size_b_other_files += file_size
    size_b_other_dirs = 0
    for folder_name, folder in root.dir_refs.items():
        folder_size = folder.total_size
        if folder_size >= min_size_b and (level <= max_level or max_level < 0):
            output += _recursive_call(
                folder, full_path_to_here=f"{full_path_to_here}{folder_name}/"
            )
            continue
        size_b_other_dirs += folder_size
    if root.total_size >= min_size_b:
        output.append(
            (
                f"{full_path_to_here}",
                "d",
                root.total_size,
                root.own_stat.st_mtime,
            )
        )
    # if size_b_other_files > 0:
    #     print_fn(f"{indent}(other files){format_b_in_mb(size_b_other_files)}")
    # if size_b_other_dirs > 0:
    #     print_fn(f"{indent}(other dirs){format_b_in_mb(size_b_other_dirs)}")
    return output
