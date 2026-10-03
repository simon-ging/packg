"""
Find duplicate files inside one folder and delete them.

Of each group of duplicates the first file in natural name order is kept. Without -w nothing
is deleted, the duplicates are only listed. Deleting is permanent.

Example: python -m packg.cli.deduplicate_within_dir /path/to/folder -m approx -w
"""

from pathlib import Path

from attr import define
from loguru import logger
from natsort import natsorted

from packg.iotools.file_dedup import DedupArgs, delete_files, find_duplicates, load_folder
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from typedparser import TypedParser, add_argument


@define(slots=False)
class Args(DedupArgs):
    folder: Path = add_argument("folder", type=str, help="Folder to search", default=None)


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    files = load_folder(Path(args.folder), args)
    duplicates = find_duplicates(
        files, files, method=args.compare_method, check_date_in_filename=args.check_date_in_filename
    )
    to_delete = natsorted({name for found in duplicates.values() for name in found})
    logger.warning(
        f"Files checked: {len(files.names)}, to delete: {len(to_delete)}, "
        f"to keep: {len(duplicates)}"
    )
    delete_files(files.folder, to_delete, args.write)
    if not args.write:
        logger.warning("Dry run. Use -w to delete the duplicates.")


if __name__ == "__main__":
    main()
