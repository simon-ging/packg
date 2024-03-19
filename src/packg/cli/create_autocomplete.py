"""
Create a bash autocompletion script for a package or several packages .

Note: If it does not find a module, maybe __init__.py is missing.

see  /usr/share/bash-completion/bash_completion complete -F _longopt complete
to figure out how to complete the 2nd argument same as cat would complete the 1st argument.

"""

from pathlib import Path
from typing import Optional

from attrs import define
from loguru import logger

from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.packaging import FILEDIR_AUTOCOMPLETE, create_new_bash_autocomplete_script
from typedparser import VerboseQuietArgs, add_argument, TypedParser


@define
class Args(VerboseQuietArgs):
    packages: str = add_argument(shortcut="-p", type=str, default="packg,visiontext")
    target_script: Optional[Path] = add_argument(
        shortcut="-t",
        type=Path,
        help="Target script. If not given, will write to ./autocomplete.sh",
    )
    run_dir: Optional[str] = add_argument(
        shortcut="-r", type=str, help="Only create autocompletion for this directory"
    )
    command_name: str = add_argument(
        shortcut="-c", type=str, default="py", help="Command name to call python"
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    packages = args.packages.split(",")
    autocomplete_script = create_new_bash_autocomplete_script(
        packages, run_dir=args.run_dir, command_name=args.command_name
    )
    if args.target_script is None:
        args.target_script = "autocomplete.sh"
    Path(args.target_script).write_text(
        "\n".join([FILEDIR_AUTOCOMPLETE, autocomplete_script]), encoding="utf-8"
    )
    logger.info(f"Created: {args.target_script}")
    logger.debug(autocomplete_script)


if __name__ == "__main__":
    main()
