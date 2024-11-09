"""Tests for gutil.system module"""

import pytest

from packg.system import systemcall, systemcall_with_assert


def test_systemcall():
    """
    Test:
    - run simple command and check returns
    """
    out, err, retcode = systemcall_with_assert("echo foo")
    assert isinstance(retcode, int) and retcode == 0
    assert out.replace("\r", "") == "foo\n"
    assert err == ""

    # check that unknown command raises error
    cmd_unk = "unknown_command_234032897324"
    with pytest.raises(AssertionError):
        systemcall_with_assert(cmd_unk)

    # check that unknown command gives back correct return values
    out, err, retcode = systemcall(cmd_unk)
    assert isinstance(retcode, int) and retcode != 0
    assert isinstance(out, str) and len(out) == 0
    assert isinstance(err, str) and len(err) > 0


def main():
    """run tests manually when calling this script"""
    test_systemcall()


if __name__ == "__main__":
    main()
