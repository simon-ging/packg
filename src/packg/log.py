"""
Wrapper for loguru package

https://loguru.readthedocs.io/en/stable/overview.html
https://loguru.readthedocs.io/en/stable/resources/recipes.html#changing-the-level-of-an-existing-handler

Usage:
    from loguru import logger
    from lmbtools.logging.console import configure_logger, SHORTEST_FORMAT

    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info("Hello")
"""
import os
import sys
from copy import deepcopy
from logging import getLevelName
from typing import Union, Optional, List, Any, Dict

from loguru import logger

LevelType = Union[str, int]  # either "DEBUG" or 10
DEFAULT_LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>")
SHORTER_FORMAT = (
    "<green>{time:YYYYMMDD HH:mm:ss}</green> <level>{level: <4.4}</level> "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
    "<level>{message}</level>")
SHORTEST_FORMAT = (
    "<green>{time:YYYYMMDD HH:mm:ss}</green> <level>{level: <4.4}</level> "
    "<level>{message}</level>")
BRIGHTBG_FORMAT = (
    "<green>{time:YYYYMMDD HH:mm:ss}</green> <level>{level: <4.4}</level> "
    "<blue>{name}</blue>:<blue>{function}</blue>:<blue>{line}</blue> "
    "<level>{message}</level>")


def configure_logger(
        level: LevelType = "DEBUG",
        sink=sys.stderr,
        format=SHORTEST_FORMAT,  # noqa
        colorize=True,
        add_sinks: Optional[List[Any]] = None,
        kwargs_handler: Optional[Dict[str, Any]] = None,
        **kwargs: Any
) -> None:
    """
    Configure the loguru logger. For more complex usages, use logger.configure() directly.

    Args:
        level: minimum level to log
        sink: where to write the logs to
        format: message formatting
        colorize: add color codes to the output
        add_sinks: other sinks to add (str will add a file sink)
        kwargs_handler: additional parameters to pass to each handler
        **kwargs: additional parameters to pass to logger.configure()

    References:
        https://loguru.readthedocs.io/en/stable/api/logger.html
        from loguru import _colorizer  # color code reference

    """
    add_sinks = add_sinks if add_sinks is not None else []
    kwargs_handler = kwargs_handler if kwargs_handler is not None else {}
    sinks = [sink] + add_sinks
    handlers = []
    for lsink in sinks:
        params = {"sink": lsink, "format": format, "colorize": colorize,
                  "level": get_level_as_str(level)}
        assert "sink" not in kwargs_handler, f"sink is a reserved key, got {params}"
        params.update(deepcopy(kwargs_handler))
        if isinstance(lsink, str):
            # automatically disable color codes for files
            params["colorize"] = False
        handlers.append(params)

    # fix bug when combining colorama and loguru in conemu console on windows
    if (colorize and os.name == "nt" and os.environ.get("CONEMUANSI") == "ON"
            and sink in (sys.stderr, sys.stdout)):
        print("\r", end="")  # the invisible print here magically fixes the color
    logger.configure(handlers=handlers, **kwargs)


def get_level_as_str(level: LevelType):
    if isinstance(level, str):
        return level.upper()
    if isinstance(level, int):
        return getLevelName(level).upper()
    raise TypeError(f"Level must be str or int, not {type(level)}")


def get_logger_level_from_args(args) -> str:
    if args.verbose:
        return "DEBUG"
    if args.quiet:
        return "WARNING"
    return "INFO"


def get_terminal_size() -> int:
    try:
        n_cols = os.get_terminal_size().columns
    except OSError:
        n_cols = 80
    return n_cols

# # catch logs - code below will raise exceptions for logs. helpful for debugging where
# # random logs are coming from
# import logging
#
#
# class CustomHandler(logging.Handler):
#     def __init__(self):
#         super().__init__()
#
#     def emit(self, record):
#         raise RuntimeError("Caught log message: {}".format(record.getMessage()))
#
#
# err_logger = logging.getLogger()
# err_logger.addHandler(CustomHandler())
