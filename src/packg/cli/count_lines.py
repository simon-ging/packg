"""
Count lines per file endings in a directory.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

from attrs import define
from loguru import logger

from packg import Const, format_exception
from packg.iotools import make_index
from packg.iotools.encoding import (
    detect_encoding_and_read_file,
    detect_encoding_if_needed_and_read_file,
)
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.tqdmext import tqdm_max_ncols
from typedparser import TypedParser, VerboseQuietArgs, add_argument


class SortC(Const):
    NAME = "name"
    LINES = "lines"


@define
class Args(VerboseQuietArgs):
    folder: Path = add_argument("folder", type=str, help="Directory to check")
    ignore_case: bool = add_argument(shortcut="-i", action="store_true", help="Ignore case")
    endings: Optional[list[str]] = add_argument(
        shortcut="-e", action="append", help="count files with these endings"
    )
    write_fix: bool = add_argument(
        shortcut="-w", action="store_true", help="Write files with fixed encoding"
    )
    check_all: bool = add_argument(
        shortcut="-a", action="store_true", help="Check all files for encoding"
    )
    depth: int = add_argument(shortcut="-d", type=int, default=0, help="Depth to display")
    show_files: bool = add_argument(
        shortcut="-f", action="store_true", help="Show files in each dir"
    )
    sort: str = add_argument(
        shortcut="-s",
        type=str,
        default=SortC.NAME,
        help=f"what to sort by",
        choices=list(SortC.values()),
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    if args.endings is None or len(args.endings) == 0:
        raise ValueError("No endings provided, use e.g. -e py -e ipynb")
    endings_set = set(args.endings)

    folder = Path(args.folder)
    if not folder.is_dir():
        raise ValueError(f"Not a dir: {folder}")

    file_index = make_index(folder)
    print()
    ending2filenames = defaultdict(list)
    for filename in file_index.keys():
        splits = Path(filename).name.split(".")
        if len(splits) == 1:
            ending = ""
        else:
            ending = splits[-1]
        if ending not in endings_set:
            continue
        if args.ignore_case:
            ending = ending.lower()
        ending2filenames[ending].append(filename)
    ending2filenames = dict(ending2filenames)
    for ending, filenames in ending2filenames.items():
        num_lines_per = defaultdict(int)
        files_per = defaultdict(int)
        for filename in tqdm_max_ncols(filenames, desc=ending):
            file_parts = filename.split("/")
            if not args.show_files:
                file_parts = file_parts[:-1]
            base_dir = "/".join(file_parts[: args.depth])
            if base_dir == "":
                base_dir = "."

            full_file = folder / filename
            try:
                if args.check_all:
                    content, encoding = detect_encoding_and_read_file(full_file)
                else:
                    content, encoding = detect_encoding_if_needed_and_read_file(full_file)
            except ValueError as e:
                logger.error(f"Failed reading file: {format_exception(e)}")
                continue

            content_unix = content.replace("\r\n", "\n")

            # count lines in content
            if ending == "ipynb":
                num_lines = count_lines_in_ipynb_str(content)
            else:
                num_lines = len(content_unix.splitlines())
            num_lines_per[base_dir] += num_lines
            files_per[base_dir] += 1
            if encoding in set(("utf-8", "ascii", None)) and content == content_unix:
                # file is already fine
                continue
            # file should be fixed
            win_lineendings = content.count("\r\n")
            msg = f"encoding={encoding} win_lineendings={win_lineendings} full_file={full_file}"
            if not args.write_fix:
                logger.warning(f"{msg} - would fix but no -w/--write_fix")
                continue
            logger.warning(f"{msg} - fixing")
            full_file.write_text(content_unix, encoding="utf-8")

        if args.sort == SortC.NAME:
            pass
        elif args.sort == SortC.LINES:
            num_lines_per = dict(sorted(num_lines_per.items(), key=lambda x: x[1], reverse=True))
        else:
            raise ValueError(f"Unknown sort: {args.sort}, must be one of {list(SortC.values())}")
        lines_per_str_list = []
        for bd, nl in num_lines_per.items():
            lines_per_str_list.append(f"{nl:10_d} {files_per[bd]:7_d} {bd}")

        lines_per_str = "\n".join(lines_per_str_list)
        print(
            f"{ending:8s} L   files dir\n{sum(num_lines_per.values()):10_d} {len(filenames):7_d} "
            f"total\n\n{lines_per_str}"
        )


def count_lines_in_ipynb_str(ipynb_content: str):
    """
    count only code, not metadata, outputs, markdown etc.
    """
    data = json.loads(ipynb_content)
    cells = data["cells"]
    n_lines = 0
    for i, cell in enumerate(cells):
        if cell["cell_type"] == "code":
            lines_withends: list[str] = cell["source"]
            n_lines += len(lines_withends)
        # if new_cell["cell_type"] == "markdown":
    return n_lines


if __name__ == "__main__":
    main()
