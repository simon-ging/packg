"""
Create a bash autocompletion script for a package or several packages .

Note: If it does not find a module, maybe __init__.py is missing.
"""

from pathlib import Path
from typing import Optional

import importlib_resources
from loguru import logger

from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.packaging import create_bash_autocomplete_script
from typedparser import VerboseQuietArgs, add_argument, define, TypedParser


@define
class Args(VerboseQuietArgs):
    package: str = add_argument("package", type=str)
    target_script: Optional[Path] = add_argument(
        shortcut="-t",
        type=Path,
        help="Target script. If not given, will write to (package_directory)/autocomplete.sh",
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    autocomplete_script = create_bash_autocomplete_script(args.package)
    if args.target_script is None:
        args.target_script = importlib_resources.files(args.package) / "autocomplete.sh"
    Path(args.target_script).write_text(autocomplete_script, encoding="utf-8")
    logger.info(f"Created: {args.target_script}")


if __name__ == "__main__":
    main()
