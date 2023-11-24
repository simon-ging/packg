import traceback
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from os import devnull


def format_exception(e, with_traceback=False) -> str:
    error_str, error_name = str(e), type(e).__name__
    if error_str == "":
        out_str = error_name
    else:
        out_str = f"{error_name}: {error_str}"

    if not with_traceback:
        return out_str

    tb_list = traceback.format_tb(e.__traceback__)
    tb_str = "".join(tb_list)
    return f"{tb_str}{out_str}"


@contextmanager
def suppress_stdout_stderr():
    """A context manager that redirects stdout and stderr to devnull"""
    with open(devnull, "w", encoding="utf-8") as fnull:
        with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
            yield err, out


def convert_unsigned_int_to_bytes(int_input:int, length:int=4) -> bytes:
    """
    convert integer to bytes

    Args:
        int_input:
        length: 4 = int32 (max 4B), 8 = int64 (max 1.9e19)

    Returns:
        bytes
    """
    return int(int_input).to_bytes(length, "big")


def convert_bytes_to_unsigned_int(bytes_input:bytes) -> int:
    """
    convert bytes to integer

    Args:
        bytes_input:

    Returns:
        integer
    """
    if len(bytes_input) == 0:
        raise ValueError("bytes_input must have length > 0 but is empty")
    return int.from_bytes(bytes_input, "big")
