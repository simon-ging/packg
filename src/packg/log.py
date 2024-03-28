"""
- Utils for the loguru package
  https://loguru.readthedocs.io/en/stable/overview.html
  https://loguru.readthedocs.io/en/stable/resources/recipes.html#changing-the-level-of-an-existing-handler
- Utils for the standard library logging package

Usage:
    from loguru import logger
    from lmbtools.logging.console import configure_logger, SHORTEST_FORMAT

    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info("Hello")
"""
from __future__ import annotations

import logging
import os
import sys
from copy import deepcopy
from logging import getLevelName
from typing import Union

from loguru import logger
from pathspec import PathSpec

from packg.iotools.pathspec_matcher import make_pathspec
from typedparser import VerboseQuietArgs

LevelType = Union[str, int]  # either "DEBUG" or 10
DEFAULT_LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)
SHORTER_FORMAT = (
    "<green>{time:YYYYMMDD HH:mm:ss}</green> <level>{level: <4.4}</level> "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
    "<level>{message}</level>"
)
SHORTEST_FORMAT = (
    "<green>{time:YYYYMMDD HH:mm:ss}</green> <level>{level: <4.4}</level> "
    "<level>{message}</level>"
)
BRIGHTBG_FORMAT = (
    "<green>{time:YYYYMMDD HH:mm:ss}</green> <level>{level: <4.4}</level> "
    "<blue>{name}</blue>:<blue>{function}</blue>:<blue>{line}</blue> "
    "<level>{message}</level>"
)
TIMELESS_FORMAT = "<level>{level: <4.4}</level> <level>{message}</level>"


def get_stdlib_logging_formatter():
    return logging.Formatter(
        "%(asctime)s %(levelname)-4s %(filename)s:%(lineno)d %(message)s",
        datefmt="%Y%m%d %H:%M:%S",
    )


global_logger_config = None


def configure_logger(
    level: LevelType = "DEBUG",
    sink=sys.stderr,
    format=SHORTEST_FORMAT,  # noqa # pylint: disable=redefined-builtin
    colorize=True,
    add_sinks: Union[list[any], list[dict[str, any]], None] = None,
    kwargs_handler: Union[dict[str, any], None] = None,
    **kwargs: any,
) -> dict[str, any]:
    """
    Configure the loguru logger. For more complex usages, use logger.configure() directly.

    Args:
        level: minimum level to log
        sink: where to write the logs to
        format: message formatting
        colorize: add color codes to the output
        add_sinks: list of other sinks to add. str sinks will write to file.
            use a dictionary to change parameters format, colorize, level separately from main sink.
        kwargs_handler: additional parameters to pass to each handler
        **kwargs: additional parameters to pass to logger.configure()

    References:
        https://loguru.readthedocs.io/en/stable/api/logger.html
        from loguru import _colorizer  # color code reference

    Returns:
        Configuration passed to logger.configure()

    """
    add_sinks = add_sinks if add_sinks is not None else []
    kwargs_handler = kwargs_handler if kwargs_handler is not None else {}
    sinks = [sink] + add_sinks
    handlers = []
    level_str = get_level_as_str(level)
    for lsink in sinks:
        if isinstance(lsink, dict):
            params = lsink
            if "format" not in params:
                params["format"] = format
            if "colorize" not in params:
                params["colorize"] = colorize
            if "level" not in params:
                params["level"] = level_str
        else:
            params = {
                "sink": lsink,
                "format": format,
                "colorize": colorize,
                "level": level_str,
            }
        assert "sink" not in kwargs_handler, f"sink is a reserved key, got {params}"
        params.update(deepcopy(kwargs_handler))
        if isinstance(lsink, str):
            # automatically disable color codes for files
            params["colorize"] = False
        handlers.append(params)

    # fix bug when combining colorama and loguru in conemu console on windows
    if (
        colorize
        and os.name == "nt"
        and os.environ.get("CONEMUANSI") == "ON"
        and sink in (sys.stderr, sys.stdout)
    ):
        print("\r", end="")  # the invisible print here magically fixes the color

    logger_config = {"handlers": handlers, **kwargs}
    logger.configure(**logger_config)
    global global_logger_config
    global_logger_config = logger_config
    return logger_config


def reroute_logger(new_sink=sys.stderr, logger_config=None, handler_num: int = 0) -> None:
    """
    Reroute a sink from one target to another. Useful for proper logging inside
    a tqdm progressbar without having to recreate the entire logger.

    Args:
        new_sink: new target
        logger_config: config created by configure_logger() function above.
            If None, use the global config.
        handler_num: index of the handler of which to change the sink

    Usage:
        logger_config = configure_logger(...)
        pbar = tqdm(...)
        reroute_logger(lambda msg: pbar.write(msg, end=""), logger_config)
        # use tqdm progressbar and logger together here
        pbar.close()
        reroute_logger(sys.stderr, logger_config)

    Notes:
        The config is modified inplace so does not need to be returned here.
        It cannot be deepcopy-ed here because sink is not pickle-able.
    """
    if logger_config is None:
        logger_config = global_logger_config
    logger_config["handlers"][handler_num]["sink"] = new_sink
    logger.configure(**logger_config)
    return logger_config


def get_level_as_str(level: LevelType):
    if isinstance(level, str):
        return level.upper()
    if isinstance(level, int):
        return getLevelName(level).upper()
    raise TypeError(f"Level must be str or int, not {type(level)}")


def get_level_as_int(level: LevelType):
    if isinstance(level, int):
        return level
    level_int = int(getLevelName(level.upper()))
    return level_int


def get_logger_level_from_args(args: VerboseQuietArgs) -> str:
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


def configure_stdlib_base_logger(
    level: LevelType = "INFO",
    format="%(levelname)s: %(message)s",  # noqa  # pylint: disable=redefined-builtin
) -> None:
    """
    Configure the standard library logger.

    Args:
        level: minimum level to log
        format: message formatting
            (see https://docs.python.org/3/library/logging.html#logrecord-attributes)
    """
    level = get_level_as_int(level)
    logging.basicConfig(level=level, format=format)


def silence_stdlib_loggers(
    search_str: str,
    regex_mode: bool = False,
    level: LevelType = logging.ERROR,
    verbose: bool = False,
):
    spec: PathSpec = make_pathspec([search_str], regex_mode=regex_mode)
    # print([p.regex for p in spec.patterns])
    level = get_level_as_int(level)
    for name in logging.root.manager.loggerDict.keys():
        loggr = logging.getLogger(name)
        if spec.match_file(name):
            loggr.setLevel(level)
            if verbose:
                print(f"Set verbosity to {level} for logger '{name}'")
