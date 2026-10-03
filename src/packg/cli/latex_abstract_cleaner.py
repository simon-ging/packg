"""
Take the copy paste of an abstract and make sure it's clean, for copy pasting it
into a submission form.
"""

import re
from pathlib import Path

from attrs import define
from loguru import logger

from packg.dtime import get_timestamp_for_filename
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from typedparser import TypedParser, VerboseQuietArgs, add_argument


@define
class Args(VerboseQuietArgs):
    file: Path | None = add_argument(shortcut="-f", type=str, help="input file")
    keep_newlines: bool = add_argument(shortcut="-k", action="store_true", help="keep newlines")


def get_user_input(keep_newlines=False):
    inps = []
    while True:
        try:
            inp = input("Input? Ctrl-C to exit. ")
        except KeyboardInterrupt:
            break
        inp = inp.strip()
        if inp != "":
            inps.append(inp)

    if keep_newlines:
        return "\n".join(inps)
    else:
        return " ".join(inps)


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")
    file = args.file
    if args.file is None:
        data = get_user_input()
    else:
        data = Path(args.file).read_text()

    repls = {"\t": " ", "``": '"', "''": '"', "  ": " "}
    if not args.keep_newlines:
        repls["\n"] = " "

    old_data = None
    while old_data != data:
        old_data = data
        for k, v in repls.items():
            data = data.replace(k, v)

    latex_to_md_regex = re.compile(r"\\href\{(.*?)\}\{(.*?)\}")
    data = latex_to_md_regex.sub(r"[\2](\1)", data)

    print("\n")
    print(data)
    tfile = Path.home() / f"abstract_{get_timestamp_for_filename()}.txt"
    print("\n")
    print(f"{tfile}")
    tfile.write_text(data, encoding="utf-8")


if __name__ == "__main__":
    main()
