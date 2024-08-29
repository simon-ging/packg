from collections import defaultdict

from attrs import define
from loguru import logger
from pathlib import Path

from packg.iotools import make_index
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from typedparser import VerboseQuietArgs, add_argument, TypedParser


@define
class Args(VerboseQuietArgs):
    folder: Path = add_argument("folder", type=str, help="Directory to check")
    ignore_case: bool = add_argument(shortcut="-i", action="store_true", help="Ignore case")


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    folder = Path(args.folder)
    if not folder.is_dir():
        raise ValueError(f"Not a dir: {folder}")

    file_index = make_index(folder)
    endings = defaultdict(int)
    for filename in file_index.keys():
        splits = Path(filename).name.split(".")
        if len(splits) == 1:
            ending = ""
        else:
            ending = splits[-1]
        if args.ignore_case:
            ending = ending.lower()
        endings[ending] += 1
    print(f"{endings}")


if __name__ == "__main__":
    main()
