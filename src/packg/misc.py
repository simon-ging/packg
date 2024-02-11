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


