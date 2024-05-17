import multiprocessing
import random
import time
from attrs import define
from loguru import logger

from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.multiproc import FnMultiProcessor
from typedparser import TypedParser, add_argument, VerboseQuietArgs


@define
class Args(VerboseQuietArgs):
    workers: int = add_argument(shortcut="-w", type=int, default=0, help="Number of workers")


# restrict logger by default, only enable verbose logging in main process (not workers)
configure_logger(level="WARNING")


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")
    multiprocessing.set_start_method("spawn")
    inputs = list(range(20))
    mp = FnMultiProcessor(
        workers=args.workers,
        target_fn=example_fn,
        with_output=True,
        desc="Multiprocessing example",
        total=len(inputs),
    )
    for i in inputs:
        mp.put(i)
    mp.run()
    mp.close()
    print(f"Example finished.")


def example_fn(number: int):
    print(f"Start function {number} on process {multiprocessing.current_process().name}")
    time.sleep(0.2 + random.random() * 0.2)
    print(f"End function {number} on process {multiprocessing.current_process().name}")


if __name__ == "__main__":
    main()
