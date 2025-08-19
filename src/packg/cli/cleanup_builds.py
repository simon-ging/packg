"""
Remove build artifacts (like __pycache__) and other clutter from a directory.
"""

import shutil
from pathlib import Path

from attrs import define
from loguru import logger

from packg import format_exception
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from typedparser import TypedParser, VerboseQuietArgs, add_argument


@define
class Args(VerboseQuietArgs):
    folder: Path = add_argument("folder", type=str, help="Directory to check")
    write: bool = add_argument(shortcut="-w", action="store_true", help="Confirm removing files")
    clean_packages: bool = add_argument(
        shortcut="-p", action="store_true", help="remove package builds and dist"
    )
    clean_pycache: bool = add_argument(
        shortcut="-c", action="store_true", help="remove all pycache and pytests cache"
    )
    clean_rust: bool = add_argument(shortcut="-r", action="store_true", help="remove rust builds")
    clean_all: bool = add_argument(shortcut="-a", action="store_true", help="remove everything")
    clean_latex: bool = add_argument(
        shortcut="-l", action="store_true", help="remove latex build artifacts"
    )
    remove_empty_dirs: bool = add_argument(
        shortcut="-e", action="store_true", help="remove empty directories"
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    base_dir = args.folder.resolve()
    logger.warning(f"Cleaning up: {base_dir}")

    def rmtree_verbose(path: Path):
        logger.info(f"RM {args.write} {path}")
        if args.write:
            # shutil.rmtree(path, ignore_errors=True)
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    glob_strs = []
    if args.clean_packages or args.clean_all:
        glob_strs = ["**/build", "**/dist", "**/*.egg-info"]

    if args.clean_pycache or args.clean_all:
        glob_strs += ["**/__pycache__", "**/.pytest_cache", "**/*.pyc", "**/*.pyo"]

    if args.clean_rust or args.clean_all:
        glob_strs += ["**/*.abi3.so", "**/Cargo.lock"]

    if args.clean_latex or args.clean_all:
        glob_strs += ["**/*.aux", "**/*.log", "**/*.out", "**/*.bbl", "**/*.blg", "**/*.synctex.gz"]

    if args.clean_all:
        glob_strs += ["**/.ipynb_checkpoints"]

    logger.info(f"Searching for {glob_strs}")
    n_removed = 0
    for glob_str in glob_strs:
        for file in base_dir.glob(glob_str):
            rmtree_verbose(file)
            n_removed += 1

    logger.info(f"Removed {n_removed} files or dirs")
    if len(glob_strs) == 0 and not args.remove_empty_dirs:
        logger.warning("No operation specified")

    if args.remove_empty_dirs or args.clean_all:
        remove_empty_dirs(base_dir, write=args.write)

    if not args.write:
        logger.warning("Test run (no -w), did not do anything.")


def remove_empty_dirs(folder, level=0, write=False, ignore_errors=True):
    # recursively delete empty subfolders
    subfolders = [f for f in list(folder.glob("*")) if f.is_dir() and not f.is_symlink()]
    for subfolder in subfolders:
        remove_empty_dirs(subfolder, level=level + 1, write=write)

    # if nothing remains, delete this folder
    remaining_elements = list(folder.glob("*"))
    if len(remaining_elements) == 0:
        logger.info(f"RM empty dir: {folder}")
        if write:
            if ignore_errors:
                try:
                    folder.rmdir()
                except OSError as e:
                    logger.error(f"{format_exception(e)}\nwhen removing {folder}")
            else:
                folder.rmdir()


if __name__ == "__main__":
    main()
