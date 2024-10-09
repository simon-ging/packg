import io
import logging

from packg.log import silence_stdlib_loggers


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
import pytest
from packg.log import configure_logger

def test_configure_logger():
    config = configure_logger(level="INFO")
    assert config["handlers"][0]["level"] == "INFO"
