"""
Find files of the source folder that also exist in the target folder, and delete them on one
side.

Without --delete_source or --delete_target the duplicates are only listed, and without -w
nothing is deleted. Deleting is permanent.

Example:
    python -m packg.cli.deduplicate_between_dirs /path/to/source /path/to/target --delete_source -w
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
    src: Path = add_argument(positional=True, type=str, help="Source base dir", default=None)
    tgt: Path = add_argument(positional=True, type=str, help="Target base dir", default=None)
    delete_source: bool = add_argument(action="store_true", help="Delete dups in source")
    delete_target: bool = add_argument(action="store_true", help="Delete dups in target")


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")
    if args.delete_source and args.delete_target:
        raise ValueError("Cannot delete in both source and target because then nothing remains.")

    src = load_folder(Path(args.src), args)
    tgt = load_folder(Path(args.tgt), args)
    duplicates = find_duplicates(
        src, tgt, method=args.compare_method, check_date_in_filename=args.check_date_in_filename
    )
    src_dups = natsorted(duplicates.keys())
    tgt_dups = natsorted({name for found in duplicates.values() for name in found})
    logger.info(f"Duplicates: {len(src_dups)} files in source, {len(tgt_dups)} in target")
    if args.delete_source:
        delete_files(src.folder, src_dups, args.write)
    if args.delete_target:
        delete_files(tgt.folder, tgt_dups, args.write)
    if (args.delete_source or args.delete_target) and not args.write:
        logger.warning("Dry run. Use -w to delete the duplicates.")


if __name__ == "__main__":
    main()
