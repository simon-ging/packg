"""
Create a bash autocompletion script.

Given the files __main__.py and pyproject.toml, after installation,
the command `packg my.module` will run `python -m packg.my.module`.
This script will create the autocompletion script over all modules in the package.
"""

import importlib
from pathlib import Path
from typing import Optional

from attrs import define
from loguru import logger

from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.packaging import FILEDIR_AUTOCOMPLETE, create_bash_autocomplete_script
from typedparser import TypedParser, VerboseQuietArgs, add_argument


@define
class Args(VerboseQuietArgs):
    packages: str = add_argument(shortcut="-p", type=str, default="packg,visiontext")
    run_dir: Optional[str] = add_argument(
        shortcut="-r", type=str, help="Only create autocompletion for this directory"
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    packages = args.packages.split(",")
    for package in packages:
        mod = importlib.import_module(package)
        # print(mod.__file__)
        autocomplete_file = Path(mod.__file__).parent.parent.parent / f"autocomplete_{package}.sh"
        autocomplete_script = create_bash_autocomplete_script(
            package, command_name=package, run_dir=args.run_dir
        )
        Path(autocomplete_file).write_text(
            "\n".join([autocomplete_script, FILEDIR_AUTOCOMPLETE]), encoding="utf-8"
        )
        logger.info(f"Created: {autocomplete_file}")
    # logger.debug(autocomplete_script)


if __name__ == "__main__":
    main()
