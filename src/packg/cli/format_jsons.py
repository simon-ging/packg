"""
Format all JSON files in a directory tree with consistent indentation.
"""

import json
from pathlib import Path

from attrs import define
from loguru import logger

from packg.iotools.jsonext import dump_json, load_json
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from typedparser import TypedParser, VerboseQuietArgs, add_argument


@define
class Args(VerboseQuietArgs):
    folder: Path = add_argument("folder", type=str, help="Directory to search for JSON files")
    write: bool = add_argument(
        shortcut="-w", action="store_true", help="Write formatted JSON files"
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")
    root = args.folder.resolve()
    logger.info(f"Searching for JSON files in: {root}")
    formatted_count = 0
    skipped_count = 0
    for path in root.glob("**/*.json"):
        try:
            data = load_json(path)
            if args.write:
                dump_json(data, path, indent=2, ensure_ascii=False)
                logger.info(f"Formatted: {path}")
            else:
                logger.info(f"Would format: {path}")
            formatted_count += 1
        except json.JSONDecodeError as e:
            logger.warning(f"Skipping invalid JSON: {path} ({e})")
            skipped_count += 1
    logger.info(f"Formatted {formatted_count} files, skipped {skipped_count} files")
    if not args.write:
        logger.warning("Test run (no -w), did not modify any files.")


if __name__ == "__main__":
    main()
