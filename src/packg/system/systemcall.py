"""Helper to run system commands and process their output."""

from __future__ import annotations

import subprocess
from typing import Optional, Tuple, Union


def systemcall(
    call: Union[str, list[str]],
    verbose: bool = False,
    decode: Optional[str] = "utf-8",
    shell: bool = True,
) -> Tuple[str, str, int]:
    """Run a command with subprocess.Popen and process the output. This call
    is synchronous so output will only returned once the command is done.

    Args:
        call: the command to run
        verbose: verbosity (0=quiet)
        decode: decode the output with this encoding
        shell: run the command in a shell

    Returns:
        stdout, stderr, returncode
    """
    pipe = subprocess.PIPE
    with subprocess.Popen(call, stdout=pipe, stderr=pipe, shell=shell) as process:
        out, err = process.communicate()
        retcode = process.poll()
    if decode is not None:
        out = out.decode(decode)
        err = err.decode(decode)
    if verbose:
        print(f"out {out} err {err} ret {retcode}")
    return out, err, retcode


def assert_command_worked(errmsg: str, cmd: str, out: str, err: str, retcode: int) -> None:
    """Process the output of a systemcall and assert that the command worked.

    Args:
        errmsg: additional error info to display
        cmd: original command that was run (for display purposes)
        out: stdout of the command
        err: stderr of the command
        retcode: return code of the command

    Returns:
        None

    """
    assert retcode == 0, (
        f"command failed: {cmd}\nout: {out}\nerr: {err}\n"
        f"retcode: {retcode}\n"
        f"additional error info: {errmsg}"
    )


def systemcall_with_assert(
    call: Union[str, list[str]],
    errmsg: str = "none",
    verbose: bool = False,
    decode: Optional[str] = "utf-8",
    shell: bool = True,
) -> Tuple[str, str, int]:
    """Run a command and assert it worked

    Args:
        call: command to run
        errmsg: additional error info to display when the command fails
        verbose: verbosity of the command
        decode: decode the output with this encoding
        shell: run the command in a shell

    Returns:
        stdout, stderr, returncode
    """
    out, err, retcode = systemcall(call, verbose=verbose, decode=decode, shell=shell)
    assert_command_worked(errmsg, call, out, err, retcode)
    return out, err, retcode
