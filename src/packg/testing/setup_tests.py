"""
Some reusable fixtures and example setups for writing the tests.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from packg.iotools.misc import set_working_directory


@pytest.fixture(scope="session", autouse=True)
def session_tmp_path():
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def git_example_fixture(session_tmp_path):
    """
    Setup a git example directory git_dir s.t. `git status --porcelain` returns
         M a
         D b
        R  c -> c2
        A  f
        ?? e

    Not using git -C git_dir because that makes adding files to the repo more difficult
    """
    git_dir = session_tmp_path / "git_example"
    setup_git_example(git_dir)
    yield git_dir


def setup_git_example(git_dir):
    os.makedirs(git_dir, exist_ok=True)

    def _write_text(p, t):
        Path(p).write_text(t, encoding="utf-8")

    def verbose_os_system(cmd):
        print("$", cmd)
        os.system(cmd)

    with set_working_directory(git_dir):
        verbose_os_system("git init")
        # author config is necessary e.g. on test job runners, otherwise git commit fails
        verbose_os_system('git config user.email "test@te.st"')
        verbose_os_system('git config user.name "Te St"')
        _write_text("a", "a")
        _write_text("b", "b")
        _write_text("c", "c")
        _write_text("d", "d")
        _write_text("g", "g")
        verbose_os_system("git add .")
        verbose_os_system("git commit -q -m initcommit")
        verbose_os_system("git log --oneline")
        _write_text("a", "a2")
        os.remove("b")
        os.rename("c", "c2")
        _write_text("e", "e")
        _write_text("f", "f")
        _write_text("g", "g2")
        verbose_os_system("git add c c2 f g")

        # verbose_os_system("git status")  # human readable
        # verbose_os_system("git status --porcelain")  # stable, short
        # out, _err, _retcode= systemcall("git status -z")  # machine readable
        # print("OUT", out.replace("\0", "\n"))
        # verbose_os_system("git add --dry-run .")  # add 'a'\nremove 'b'\n ...
