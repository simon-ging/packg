"""
Download a list of URLs

Currently this uses the last part of the URL as a filename.
"""

import os
import time
from collections import Counter
from pathlib import Path
from typing import Optional

from loguru import logger

from packg.iotools import yield_lines_from_file
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.multiproc import FnMultiProcessor
from packg.web import download_file
from typedparser import VerboseQuietArgs, add_argument, TypedParser
from attrs import define


@define
class Args(VerboseQuietArgs):
    target_dir: Optional[Path] = add_argument(
        shortcut="-t", type=str, help="Target dir", required=True
    )
    input_list: Optional[Path] = add_argument(
        shortcut="-i", type=str, help="List of URLs", required=True
    )
    filename_list: Optional[Path] = add_argument(
        shortcut="-f", type=str, help="List of filenames", default=None
    )
    prefix: Optional[str] = add_argument(shortcut="-p", type=str, help="Prefix", default=None)
    cpus: int = add_argument(shortcut="-c", type=int, help="Number of cpus", default=0)
    sleep_time: float = add_argument(shortcut="-s", type=float, help="Sleep time", default=1)
    min_size_mb: float = add_argument(shortcut="-m", type=float, help="Min size in MB", default=0.0)
    n_retries: int = add_argument(shortcut="-r", type=int, help="Number of retries", default=3)


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    input_list = list(yield_lines_from_file(args.input_list))
    logger.info(f"Found {len(input_list)} lines in {args.input_list}")
    if args.prefix is not None:
        input_list = [f"{args.prefix}{line}" for line in input_list]
    logger.info(f"First 10 URLs: {input_list[:10]}")

    # load list of filenames if exists
    if args.filename_list is not None:
        filename_list = list(yield_lines_from_file(args.filename_list))
        assert len(filename_list) == len(
            input_list
        ), f"Filename list length {len(filename_list)} != URL list length {len(input_list)}"
        url_to_file = {url: file for url, file in zip(input_list, filename_list)}
    else:
        url_to_file = {url: Path(url).name for url in input_list}

    url_status = {url: "todo" for url in input_list}
    url_to_file_here = {}
    for url, file in url_to_file.items():
        full_file = args.target_dir / file
        if full_file.is_file():
            url_status[url] = "done"
            continue
        url_to_file_here[url] = full_file
    logger.info(f"Downloading status: {Counter(url_status.values())}")

    os.makedirs(args.target_dir, exist_ok=True)
    proc = FnMultiProcessor(
        args.cpus, download_fn, total=len(url_to_file_here), desc="Downloading URLs"
    )
    for url, file in url_to_file_here.items():
        if file.is_file():
            continue
        proc.put(file, url, args.sleep_time, args.min_size_mb, args.n_retries)
    proc.run()
    outputs = []
    for _ in range(len(url_to_file_here)):
        outputs.append(proc.get())
    proc.close()


def download_fn(file, url, sleep_time, min_size_mb, n_retries):
    n_tries = 0
    while True:
        success = True
        n_tries += 1
        try:
            download_file(file, url, verbose=False, pbar=False)
        except KeyboardInterrupt:
            # delete file to avoid having half files leftover
            if file.is_file():
                file.unlink()
        if min_size_mb > 0 and Path(file).stat().st_size < min_size_mb * 1024**2:
            logger.warning(
                f"File {file} is too small, retrying after sleep. "
                f"Got: {Path(file).read_text(encoding='utf-8')}"
            )
            os.unlink(file)
            success = False
        if success:
            break
        elif n_tries >= n_retries:
            logger.error(f"Too many retries for {url} {file}")
            break
        else:
            time.sleep(sleep_time)
            continue

    time.sleep(sleep_time)
    return True


if __name__ == "__main__":
    main()
