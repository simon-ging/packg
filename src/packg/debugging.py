"""

----- Copy paste:

from attrs import define
from loguru import logger

from packg.debugging import PyCharmDebugArgs, connect_to_pycharm_debug_server
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args, logger
from typedparser import VerboseQuietArgs, add_argument, TypedParser

@define
class Args(VerboseQuietArgs, PyCharmDebugArgs):
    pass


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")
    if args.trace is not None:
        connect_to_pycharm_debug_server(args.trace, args.trace_port)

if __name__ == "__main__":
    main()

"""
import time
from typing import Optional

from attrs import define

from typedparser import add_argument


def connect_to_pycharm_debug_server(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """
    Connect to a running pycharm debug server.

    To setup in PyCharm See Debug -> Edit Configurations -> Add New Configuration ->
        Python Debug Server -> Configure port, install packages, etc. -> Run

    Then run this function at the start of your code to connect it to the server.

    Args:
        host: host or None for skipping the connection process
        port: port or None for default port 12345
    """
    if host is None:
        return
    import pydevd_pycharm  # noqa  # pylint: disable=import-error

    if port is None:
        port = 12345
    while True:
        try:
            pydevd_pycharm.settrace(
                host, port=port, stdoutToServer=True, stderrToServer=True, suspend=False
            )
            break
        except ConnectionRefusedError:
            print(f"Debug server connection refused: {host}:{port}. Retrying...")
            time.sleep(2)


@define
class PyCharmDebugArgs:
    trace: str | None = add_argument(
        type=str, help="Connect debug server on this host.", default=None
    )
    trace_port: int = add_argument(type=int, default=33553, help="Target debugging server port")
