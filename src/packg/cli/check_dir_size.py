from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib
from attr import define
from loguru import logger

from packg import Const
from packg.caching import get_joblib_memory
from packg.iotools.folder import Folder, get_subfolder_data
from packg.iotools.misc import format_b_in_gb
from packg.log import configure_logger, get_logger_level_from_args
from typedparser import TypedParser, VerboseQuietArgs, add_argument

mem: joblib.Memory = get_joblib_memory(verbose=True)


class FileSortFieldsC(Const):
    PATH = "path"
    SIZE = "size"
    MTIME = "mtime"
    TYPE = "type"


@define
class Args(VerboseQuietArgs):
    start_path: Path = add_argument(positional=True, help="Starting path")
    min_mb: float = add_argument(
        shortcut="-m", type=float, default=100, help="Minimum size in MB to show."
    )
    depth: int = add_argument(
        shortcut="-d", type=int, default=-1, help="Max nesting levels to show (-1=inf)."
    )
    reset_cache: bool = add_argument(shortcut="-r", action="store_true", help="Reset the cache.")
    sort: str = add_argument(  # TODO better error msg if this is set wrongly
        shortcut="-o",
        type=str,
        default=FileSortFieldsC.PATH,
        help=f"Sort by any of: {', '.join(FileSortFieldsC.values_list())}. "
        "Use comma-separated values to sort by multiple fields.",
        choices=FileSortFieldsC.values_list(),
    )
    inverse: bool = add_argument(
        shortcut="-i", action="store_true", help="Inverse sort (descending)."
    )
    type: Optional[str] = add_argument(
        shortcut="-t", type=str, default=None, help="Filter path type: (d)irs, (f)iles or None"
    )


def main():
    import pandas as pd  # TODO either move to visiontext, or recreate without pandas.

    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args))

    if args.reset_cache:
        get_populated_root.clear()
        logger.info("Cleared cache")

    start = Path(args.start_path).absolute().as_posix()
    logger.info(f"Finding all files in {start}")
    root = get_populated_root(start)
    # print_graph(root, max_level=args.depth, min_size_mb=args.min_mb)
    subfolder_data = get_subfolder_data(root, max_level=args.depth, min_size_mb=args.min_mb)
    # df = convert_subfolder_data_to_dataframe(subfolder_data)

    column_titles = ["path", "type", "size", "mtime"]
    df = pd.DataFrame(subfolder_data, columns=column_titles)
    df["size"] = df["size"].apply(format_b_in_gb)
    df["mtime"] = pd.to_datetime(df["mtime"], unit="s")
    df["mtime"] = df["mtime"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # sort by mtime ascending
    df = df.sort_values(by=args.sort.split(","), ascending=not args.inverse)

    if args.type is not None:
        allowed_types = ["d", "f"]
        assert args.type in allowed_types, f"Invalid type {args.type} (allowed: {allowed_types})"
        df = df[df["type"] == args.type]

    print(df.to_string(index=False))


@mem.cache(verbose=99999)
def get_populated_root(start: str):
    logger.info(f"Populating root folder {start}")
    root = Folder(start)
    root.populate(recursive=True)
    return root


def print_graph(
    root_folder: Folder,
    level: int = 0,
    max_level: int = -1,
    min_size_mb: float = 100,
    print_fn=print,
    full_path_to_here="",
):
    min_size_b = min_size_mb * 1024**2
    if max_level == 0:
        return
    size_b_other_files = 0
    for file, file_stat in root_folder.files_and_stat.items():
        file_size = file_stat.st_size
        if file_size >= min_size_b:
            print_fn(f"{format_b_in_gb(file_size):>10s} F {full_path_to_here}{file} ")
            continue
        size_b_other_files += file_size
    # if size_b_other_files > 0:
    #     print_fn(f"{indent}(other files){format_b_in_mb(size_b_other_files)}")
    size_b_other_dirs = 0
    for folder_name, folder in root_folder.dir_refs.items():
        folder_size = folder.total_size
        if folder_size > min_size_b:
            if level <= max_level or max_level < 0:
                print_graph(
                    folder,
                    level=level + 1,
                    max_level=max_level,
                    min_size_mb=min_size_mb,
                    print_fn=print_fn,
                    full_path_to_here=f"{full_path_to_here}{folder_name}/",
                )
                continue
            # print_fn(f"{format_b_in_gb(folder_size)} {full_path_to_here}{folder_name}/")
            continue
        size_b_other_dirs += folder_size
    # if size_b_other_dirs > 0:
    #     print_fn(f"{indent}(other dirs){format_b_in_mb(size_b_other_dirs)}")
    if root_folder.total_size >= min_size_b:
        print_fn(f"{format_b_in_gb(root_folder.total_size):>10s} D {full_path_to_here}")


if __name__ == "__main__":
    main()
