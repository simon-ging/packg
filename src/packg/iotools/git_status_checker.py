from pathlib import Path
from typing import Dict

from packg.iotools.file_reader import yield_nonempty_stripped_lines
from packg.iotools.misc import set_working_directory
from packg.system import systemcall_with_assert
from packg.typext import PathType


def get_gitadd_dryrun_output(base_dir):
    with set_working_directory(base_dir):
        out, _err, _retcode = systemcall_with_assert("git add --dry-run .")
    return out


def parse_gitadd_dryrun_output(
    output: str, base_dir: PathType, return_relative_paths: bool = True
) -> Dict[str, str]:
    """
    Parse the output of git add --dry-run . into a dict of files and their status.

    Notes:
        Alternative way to do this would be git status: https://git-scm.com/docs/git-status#_output
    """
    files = {}
    for line in yield_nonempty_stripped_lines(output.splitlines()):
        line_split = line.split(" ")
        status = line_split[0].strip()
        file = " ".join(line_split[1:]).strip()[1:-1]
        file_pth = Path(base_dir) / file
        if status == "add":
            assert (
                file_pth.exists()
            ), f"Could not find path {file_pth} given line {line} and basedir {base_dir}"
        elif status == "remove":
            assert (
                not file_pth.exists()
            ), f"Found path {file_pth} given line {line} and basedir {base_dir}"
        else:
            raise ValueError(f"Unknown status {status}")

        file_return = file_pth.as_posix()
        if return_relative_paths:
            file_return = Path(file).as_posix()
        files[file_return] = status
    return files


def check_for_stages(base_dir):
    """
    Check if there are staged files in the given directory.

    Returns:
        Non-empty string if there are staged files, "" otherwise
    """
    with set_working_directory(base_dir):
        out, _err, _retcode = systemcall_with_assert("git diff --staged --name-only")
    return out.strip()


def check_for_unpushed_commits(base_dir):
    """
    Check if there are unpushed commits in the given directory.

    Returns:
        Non-empty string if there are staged files, "" otherwise
    """
    with set_working_directory(base_dir):
        out, _err, _retcode = systemcall_with_assert("git log --branches --not --remotes")
    return out.strip()


def get_gitstatusz_output(base_dir):
    with set_working_directory(base_dir):
        out, _err, _retcode = systemcall_with_assert("git status -z")
    return out


def parse_gitstatusz_output(output):
    """
    Currently unused!
    Parse the output of git status -z into a dict of files and their status.

    output:
        {path: [x, y, source_path or None]}
        source_path will be filed if path was renamed or copied to source_path

    """
    files = {}
    lines = output.split("\x00")
    c_pos = 0
    while True:
        try:
            line = lines[c_pos]
        except IndexError:
            break
        if line.strip() == "":
            c_pos += 1
            continue
        print(f"{c_pos}: {line}")
        assert line[2] == " ", f"Expected line to start with 'XY ' but got {line}"
        x, y, path = line[0], line[1], line[3:]
        other_path = None
        if x in "RC" or y in "RC":
            # for rename and copy the next line contains the other path without status
            other_path = lines[c_pos + 1]
            c_pos += 1
        files[path] = [x, y, other_path]
        c_pos += 1
    return files
