import io
import logging

import pytest

from packg.log import configure_logger, get_logger_level_from_args, silence_stdlib_loggers
from typedparser import TypedParser, VerboseQuietArgs


def test_silence_stdlib_loggers():
    # create logger that logs to a stringio stream
    logger1 = logging.getLogger("some_package.module1")
    logger1.setLevel(logging.INFO)
    stream = io.StringIO()
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    logger1.addHandler(console_handler)

    # log a message and check it was received
    mesg = "This is a log message"
    logger1.info(mesg)
    print(f"Logger stream content: '{stream.getvalue()}'")
    assert mesg in stream.getvalue()

    # change log level and check the change
    assert logger1.level == logging.INFO
    silence_stdlib_loggers("some_package*", regex_mode=False, level=logging.WARNING)
    assert logger1.level == logging.WARNING

    # log a message and check that it is now not received anymore
    stream.seek(0)
    stream.truncate()
    logger1.info("This is a hidden log message")
    print(f"Logger stream content: '{stream.getvalue()}'")
    assert stream.getvalue() == ""

    print(f"Done")


def test_configure_logger():
    config = configure_logger(level="INFO")
    assert config["handlers"][0]["level"] == "INFO"


def _parse_verbose_quiet_args(argv):
    return TypedParser.create_parser(VerboseQuietArgs, strict=True).parse_args(argv)


@pytest.mark.parametrize(
    "argv, expected_level",
    [
        ([], "INFO"),
        # each -v steps the level up (more verbose), clamped at the loudest end
        (["-v"], "DEBUG"),
        (["-vv"], "TRACE"),
        (["-vvv"], "TRACE"),
        # each -q steps the level down (quieter), clamped at the quietest end
        (["-q"], "WARNING"),
        (["-qq"], "ERROR"),
        (["-qqq"], "CRITICAL"),
        (["-qqqq"], "CRITICAL"),
        # -v and -q net out against each other
        (["-vv", "-q"], "DEBUG"),
        (["-v", "-qq"], "WARNING"),
        # explicit loglevel
        (["--loglevel", "ERROR"], "ERROR"),
    ],
)
def test_get_logger_level_from_args(argv, expected_level):
    args = _parse_verbose_quiet_args(argv)
    assert get_logger_level_from_args(args) == expected_level


def test_get_logger_level_from_args_counts_accumulate():
    args = _parse_verbose_quiet_args(["-vvv"])
    assert args.verbose == 3
    assert args.quiet == 0
    args = _parse_verbose_quiet_args(["-qq"])
    assert args.quiet == 2
    assert args.verbose == 0


@pytest.mark.parametrize("argv", [["-v", "--loglevel", "DEBUG"], ["-q", "--loglevel", "WARNING"]])
def test_get_logger_level_from_args_conflicting_loglevel(argv):
    args = _parse_verbose_quiet_args(argv)
    with pytest.raises(AssertionError):
        get_logger_level_from_args(args)
