"""
Examples

python -m packg.cli.regex_rename /path/to/dir "search" "sub" -w

Notes:
    Use () to build groups 1, 2...
    then use \1, \2... in the sub string to fill in the groups
    https://stackoverflow.com/questions/55855922/python-renaming-file-with-regex

"""

import os
import re
from pathlib import Path

from attr import define
from loguru import logger

from packg.iotools import sort_file_paths_with_dirs_separated
from packg.iotools.file_indexer import make_index
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from typedparser import TypedParser, VerboseQuietArgs, add_argument

from packg.iotools.folder import Folder


@define
class Args(VerboseQuietArgs):
    start_path: str = add_argument("start_path", type=str, help="Starting path", default=".")
    search: str = add_argument("search", type=str)
    sub: str = add_argument("sub", type=str)
    write: bool = add_argument(shortcut="-w", action="store_true", help="Write changes to disk")
    dirs: bool = add_argument(
        shortcut="-d", action="store_true", help="Rename dirs instead of files"
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    start = Path(args.start_path).absolute().as_posix()

    if args.dirs:
        logger.info(f"Finding all dirs in {start} without recursion")
        index = dict(Folder(args.start_path).get_dir_index(max_level=0))
        logger.info(f"Found {len(index)} dirs")
    else:
        logger.info(f"Finding all files in {start}")
        index = make_index(start)
        logger.info(f"Found {len(index)} files")

    files = sort_file_paths_with_dirs_separated(index.keys())
    re_s = re.compile(args.search_index)
    for file in files:
        filep = Path(file)
        filen = filep.name
        logger.debug(file)
        filen2 = re_s.sub(args.sub, filen)
        if filen2 == filen:
            continue
        logger.info(f"{filen} -> {filen2} in {filep.parent}")
        if args.write:
            os.rename(start / filep, start / filep.parent / filen2)


if __name__ == "__main__":
    main()
