import traceback
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from os import devnull


@contextmanager
def suppress_stdout_stderr():
    """A context manager that redirects stdout and stderr to devnull"""
    with open(devnull, "w", encoding="utf-8") as fnull:
        with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
            yield err, out


def uncollate(batch):
    assert len(batch) == 1, f"Expected batch size 1 but got {len(batch)}"
    return batch[0]


def format_exception(
    e: BaseException, with_traceback: bool = False, with_source: bool = False
) -> str:
    error_str, error_name = str(e), type(e).__name__
    if error_str == "":
        out_str = error_name
    else:
        out_str = f"{error_name}: {error_str}"

    if with_source:
        if e.__traceback__ is None:
            out_str = f"{out_str} @ <no traceback>"
        else:
            tb = e.__traceback__
            while tb.tb_next is not None:
                tb = tb.tb_next
            frame = tb.tb_frame
            out_str = f"{out_str} @ {frame.f_code.co_filename}:{tb.tb_lineno}"

    if not with_traceback:
        return out_str

    if e.__traceback__ is None:
        return f"{out_str} (no traceback found to format)"
    tb_str = "".join(traceback.format_tb(e.__traceback__))
    return f"{tb_str}{out_str}"


def format_exception_with_chain(
    e: BaseException,
    with_traceback: bool = False,
    with_source: bool = False,
) -> str:
    """
    cause[0] = root cause
    cause[n] = top-level exception
    """
    chain = []
    cur = e
    while cur is not None:
        chain.append(cur)
        cur = cur.__cause__ or cur.__context__

    chain.reverse()  # root -> top

    parts = []
    for i, exc in enumerate(chain):
        parts.append(
            f"cause[{i}]: "
            f"{format_exception(exc, with_traceback=with_traceback, with_source=with_source)}"
        )

    return " | ".join(parts)
