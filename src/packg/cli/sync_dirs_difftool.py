"""
Compare 2 directories.

TODO
    would be alot faster with hashing
    allow bidirectiomnal, or flag for switch source and dst
"""

import difflib
import os
import shutil
from pathlib import Path
from typing import Counter

from attr import define
from colorama import Fore
from colorama import init as colorama_init
from loguru import logger

from packg.iotools import file_indexer
from packg.iotools.pathspec_matcher import PathSpecArgs
from packg.log import TIMELESS_FORMAT, configure_logger, get_logger_level_from_args
from packg.tqdmext import tqdm_max_ncols
from typedparser import TypedParser, VerboseQuietArgs, add_argument


@define
class Args(PathSpecArgs, VerboseQuietArgs):
    src: Path = add_argument("src", type=Path, help="Source directory.")
    dst: Path = add_argument("dst", type=Path, help="Destination directory.")
    detect_gitignore: bool = add_argument(
        action="store_true", help="Apply gitignore files if they exist."
    )
    write: bool = add_argument(shortcut="-w", action="store_true", help="Write changes.")
    move: bool = add_argument(
        action="store_true", help="Move files instead of copying (only with --write)."
    )
    diff: bool = add_argument(action="store_true", help="Show diffs.")
    reverse: bool = add_argument(action="store_true", help="Reverse the sort.")
    symmetric: bool = add_argument(shortcut="-s", action="store_true", help="Sync both ways.")
    follow_symlinks: bool = add_argument(
        action="store_true", help="Follow symlinked dirs and files."
    )
    copy_target: Path | None = add_argument(
        shortcut="-c", help="Copy to this dir, instead of overwriting args.dst."
    )


def find_gitignore_upwards(start_dir):
    # TODO turn into find file upwards, and put it where the navigate_to_git_root() fn is.
    src_gitignore_file = Path(start_dir) / ".gitignore"
    n_tries = 0
    while not src_gitignore_file.is_file():
        old_src_gitignore_file = src_gitignore_file
        src_gitignore_file = src_gitignore_file.parent.parent / ".gitignore"
        if src_gitignore_file.is_file():
            break
        if old_src_gitignore_file == src_gitignore_file or n_tries > 100:
            raise FileNotFoundError(
                f"Passed --detect_gitignore but file not found at {src_gitignore_file.as_posix()} "
                f"after searching upwards at {start_dir} and trying {n_tries} times."
            )
        n_tries += 1
    return src_gitignore_file


def main():
    typed_parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = typed_parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=TIMELESS_FORMAT)
    colorama_init()

    if args.detect_gitignore:
        if args.exclude_gitignore_file is not None:
            raise ValueError("Cannot both autodetect gitignore and pass a gitignore file")
        src_gitignore_file = find_gitignore_upwards(args.src)
        if args.symmetric:
            # in symmetric case we must check that the target gitignore exists and is the same
            tar_gitignore_file = find_gitignore_upwards(args.dst)
            if not tar_gitignore_file.is_file():
                raise FileNotFoundError(
                    f"Passed --detect_gitignore but file not found at {tar_gitignore_file.as_posix()}"
                )
            src_gitignore_content = src_gitignore_file.read_text(encoding="utf-8")
            tar_gitignore_content = tar_gitignore_file.read_text(encoding="utf-8")
            if src_gitignore_content != tar_gitignore_content:
                raise ValueError(
                    f"Different gitignore contents for symmetric sync. Synchronize the gitignore files first. {src_gitignore_file} != {tar_gitignore_file}"
                )
        args.exclude_gitignore_file = src_gitignore_file

    def _create_index(pth):
        file_dict = file_indexer.make_index(
            pth, pathspec_args=args, follow_symlinks=args.follow_symlinks
        )
        logger.info(f"---------- Checking {pth}: Found {len(file_dict)} files.")
        logger.info(f"{len(file_dict)} left after applying all ignores.")
        for file in file_dict:
            logger.debug(f"    {file}")
        return file_dict

    logger.info(f"Indexing source dir: {args.src}")
    src_d = _create_index(args.src)
    logger.info(f"Indexing destination dir: {args.dst}")
    dst_d = _create_index(args.dst)

    copy_tasks, sames = _get_copy_tasks(
        args.src,
        src_d,
        args.dst,
        dst_d,
        is_async=not args.symmetric,
        reverse=args.reverse,
        diff=args.diff,
    )
    logger.info(f"Got {len(copy_tasks)} copy tasks.")
    statuses = [x[3] for x in copy_tasks]
    counter = Counter(statuses)
    for status, count in counter.most_common():
        logger.info(f"  {count:5d} : {status}")

    pbar = tqdm_max_ncols(total=len(copy_tasks), desc="Copying")
    for key, src, dst, copy_reason in copy_tasks:
        src_file = Path(src) / key
        dst_file = Path(dst) / key
        if args.copy_target is not None:
            dst_file = Path(args.copy_target) / key
        verb = "Moving" if args.move else "Copying"
        if args.verbose:
            pbar.write(f"{verb} {src_file} -> {dst_file}")
        if args.write:
            os.makedirs(dst_file.parent, exist_ok=True)
            if args.move:
                shutil.move(src_file, dst_file)
            else:
                shutil.copy2(src_file, dst_file)
        pbar.update()
    pbar.close()

    if not args.write:
        logger.info("No changes performed, missing -w/--write")


def _get_copy_tasks(
    src_base, src_dict, dst_base, dst_dict, is_async=True, reverse=False, diff=False
):
    # TODO this would need status report like in backuper
    src_keys = set(src_dict.keys())
    dst_keys = set(dst_dict.keys())
    all_keys = src_keys | dst_keys
    logger.info(f"---------- Found {len(all_keys)} files.")
    copy_tasks = []
    sames = []
    # pbar = tqdm_max_ncols(total=len(all_keys), desc="Checking files")
    for key in list(sorted(all_keys, reverse=reverse)):
        # pbar.set_description(f"To update: {len(copy_tasks)}")
        # pbar.update(1)
        if key not in src_dict:
            if is_async:
                logger.debug(f"Ignore missing in src:      {key}")
            else:
                logger.debug(f"Copy dst -> missing in src: {key}")
                copy_tasks.append((key, dst_base, src_base, "missing_in_src"))
        elif key not in dst_dict:
            logger.debug(f"Copy src -> missing in dst: {key}")
            copy_tasks.append((key, src_base, dst_base, "missing_in_dst"))
        else:
            modtime_src = src_dict[key][1]
            modtime_dst = dst_dict[key][1]
            size_src = src_dict[key][0]
            size_dst = dst_dict[key][0]
            if size_src == size_dst:
                # compare contents
                size_mb = size_src / 1024**2
                if size_mb > 100:
                    logger.debug(f"{key} comparing files of size {size_mb:.3f} MB")
                content_src = (Path(src_base) / key).read_bytes()
                content_dst = (Path(dst_base) / key).read_bytes()
                if content_src == content_dst:
                    sames.append(key)
                    logger.debug(f"Same file:                  {key}")
                    continue

            if diff:
                _show_diffs(f"{dst_base}/{key}", f"{src_base}/{key}")

            if modtime_src > modtime_dst:
                logger.info(f"Copy newer src -> dst:      {key}")
                copy_tasks.append((key, src_base, dst_base, "newer_in_src"))
            elif modtime_src < modtime_dst:
                if is_async:
                    logger.info(f"Ignore newer dst:           {key}")
                else:
                    logger.info(f"Copy newer dst -> src:      {key}")
                    copy_tasks.append((key, dst_base, src_base, "newer_in_dst"))
            else:
                assert size_src == size_dst, f"Size mismatch: {key} for same modtime."
    return copy_tasks, sames


def _show_diffs(from_file, to_file):
    from_file = Path(from_file)
    to_file = Path(to_file)
    from_lines = from_file.read_text(encoding="utf-8").splitlines()
    to_lines = to_file.read_text(encoding="utf-8").splitlines()
    diff = difflib.unified_diff(from_lines, to_lines, str(from_file), str(to_file))
    diff = [l.strip() for l in diff]

    lines = list(color_diff(diff))
    for line in lines:
        print(line.strip())

    # print the file info again for easier reading bottom to top
    print()
    for line in lines[:2]:
        print(line.strip())

    print("-" * 80)


def color_diff(diff):
    for line in diff:
        if line.startswith("+"):
            yield Fore.GREEN + line + Fore.RESET
        elif line.startswith("-"):
            yield Fore.RED + line + Fore.RESET
        elif line.startswith("^"):
            yield Fore.BLUE + line + Fore.RESET
        else:
            yield line


if __name__ == "__main__":
    main()
