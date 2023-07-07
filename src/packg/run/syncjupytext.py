"""
Jupytext utility to sync notebooks with scripts.

Default: Create .py files in percent format from .ipynb files.
Use -n to create .ipynb files from .py files.
"""

import os
from pathlib import Path
from typing import Optional
from timeit import default_timer as timer
from loguru import logger
from typedparser import VerboseQuietArgs, add_argument, define, TypedParser

from packg import format_exception
from packg.iotools import make_git_pathspec
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
import time


@define
class Args(VerboseQuietArgs):
    base_dir: Optional[Path] = add_argument(
        shortcut="-b", type=str, help="Source base dir", default=".")
    continuous: bool = add_argument(
        shortcut="-c", action="store_true", help="Continuous mode")
    notebooks: bool = add_argument(
        shortcut="-n", action="store_true", help="Create notebooks from scripts")


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    if args.notebooks:
        raise NotImplementedError("Not implemented yet.")

    # gitignore like pattern that includes all ipynb but excludes checkpoints
    patterns = [
        "**/*.ipynb",
        "!**/.ipynb_checkpoints",
    ]
    spec = make_git_pathspec(patterns)

    now = time.time()
    last_sync_file = Path(os.path.expanduser("~/.cache/.jupytext_last_sync"))
    last_sync_time = 0
    if last_sync_file.is_file():
        last_sync_time = float(last_sync_file.read_text())
        logger.info(f"Last sync: {now - last_sync_time:.1f} seconds ago.")

    n_rounds = 0
    start_timer = timer()
    sleep = 60
    while True:
        try:
            n_rounds += 1
            files_to_update = []
            for file in sorted(list(spec.match_tree_files(args.base_dir))):
                moddate_file = Path(file).stat().st_mtime
                if moddate_file < last_sync_time:
                    if n_rounds == 1:
                        logger.info(f"---------- Skip {file}")
                    continue
                files_to_update.append(file)

            current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            time_delta = timer() - start_timer
            current_timedelta_str = time.strftime("%H:%M:%S", time.gmtime(time_delta))
            tstr = f"{current_time_str} running for {current_timedelta_str} (round {n_rounds:4d})"
            if len(files_to_update) == 0:
                print(f"{tstr}: Nothing to update.", end="\n" if n_rounds % 100 == 0 else "\r")
            else:
                print()
                for file in files_to_update:
                    # convert to
                    logger.info(f"---------- Update {file}")
                    os.system(f"jupytext --to py:percent {file}")
                os.makedirs(last_sync_file.parent, exist_ok=True)
                now = time.time()
                last_sync_file.write_text(str(now))
                last_sync_time = now
                print()
                logger.info(f"Done updating {len(files_to_update)} files.")
            if not args.continuous:
                break
            time.sleep(sleep)

        except (KeyboardInterrupt, AssertionError) as e:
            logger.warning(f"\nInterrupted by user or file changes: {format_exception(e)}")
            break


if __name__ == "__main__":
    main()
