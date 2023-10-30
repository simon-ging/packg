"""
Utilities for python packages.
"""
import importlib
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from loguru import logger

from packg.testing.import_from_source import recurse_modules
from packg.iotools import sort_file_paths_with_dirs_separated
from packg.misc import format_exception
from packg.strings import create_nested_abbreviations


def run_package(main_file, run_dir="run", recursive=True):
    """
    Create a command line interface for a package given a directory of scripts.

    Check the run directory, list scripts, create shortcuts, run if given shortcut.

    Args:
        main_file: __file__ attribute of __main__.py e.g.
            /path/to/lmbtools/python/lmbtools/__main__.py
        run_dir: submodule with run scripts
        recursive: if True, recursively search for scripts
    """
    main_file = Path(main_file)
    print(f"main_file: {main_file}")
    package_dir = main_file.parent
    package_name = package_dir.name
    package_scripts_dir = package_dir / run_dir
    glob_str = "**/*.py" if recursive else "*.py"
    package_scripts = [
        f.relative_to(package_scripts_dir)
        for f in package_scripts_dir.glob(glob_str)
        if not f.name.startswith("__")
    ]
    sorted_scripts = sort_file_paths_with_dirs_separated(package_scripts, dirs_first=False)
    package_scripts = [f.as_posix()[:-3].replace("/", ".") for f in sorted_scripts]
    abbrevs = create_nested_abbreviations(package_scripts)

    args = sys.argv[1:]
    if len(args) > 0:
        abbrev_arg = args[0]
        if abbrev_arg in abbrevs:
            script = abbrevs[abbrev_arg]
            target = f"{package_name}.{run_dir}.{script}"
            run_script(target, args)
            return

        target = f"{package_name}.{abbrev_arg}"
        try:
            importlib.import_module(target)
            found = True
        except ModuleNotFoundError as e:
            # must figure out whether the error is due to the module not existing
            # or due to some import failing.
            if f"'{target}'" in str(e):
                # No module named (the module we are trying to run) -> module not found
                found = False
            else:
                # No module named (some other module) -> module found, but has import error
                # run it to trigger the error
                found = True
        if found:
            run_script(target, args)
            return
        print(f"Error, script not found: {abbrev_arg} and {target}")

    print(f"Usage option 1: {package_name} shortcut [args]")
    print(f"Usage option 2: {package_name} path.to.module [args]")
    print()
    print(f"shortcut   script")
    for abbrev, f in abbrevs.items():
        print(f"{abbrev:10s} {run_dir}.{f}")


def run_script(target, args):
    cmd = ["python", "-m", target, *args[1:]]
    print(f"$ {' '.join(cmd)}")

    subprocess.run(cmd)

    # # run by importing main() function
    # print(f"Running {target}")
    # sys.argv = [sys.argv[0]] + args[1:]
    # module = importlib.import_module(target)
    # main = getattr(module, "main")
    # main()


def _recurse_modules_remove_root_package(package: str, packages_only: bool = False):
    for candidate in recurse_modules(package, packages_only=packages_only):
        if candidate == package:
            continue
        candidate = candidate.removeprefix(f"{package}.")
        if candidate == "__main__":
            continue
        yield candidate


def create_bash_autocomplete_script(
    package: str, function_name: str = None, command_name: str = None
) -> str:
    """
    Create a bash script for autocompletion of a python package.

    Workflow where this is useful:
    - src/packg/__main__.py calls run_package, so `python -m packg run.script` has the same effect
    as `python -m packg.run.script`
    - pyproject.toml defines script [project.scripts] packg = "packg.__main__:main"
    so now `packg run.script` has the same effect.
    - this function now can be used to create src/packg/autocomplete.sh which, when sourced,
    provides autocompletion for the `packg` command.

    Args:
        package: package to create the autocomplete for
        function_name: default _{package}
        command_name: default {package}

    Returns:

    """
    if function_name is None:
        function_name = f"_{package}"
    if command_name is None:
        command_name = package
    packages_only = set(_recurse_modules_remove_root_package(package, packages_only=True))
    all_modules = set(_recurse_modules_remove_root_package(package))
    output_modules = []

    for m in sorted(all_modules):
        if m in packages_only:
            if f"{m}.__main__" not in all_modules:
                logger.info(f"SKIP package: {m}")
                continue
            logger.info(f"ADD package (has __main__): {m}")
        if m.endswith("__main__"):
            logger.info(f"SKIP __main__ file: {m}")
            continue
        output_modules.append(m)

    output_modules.sort()

    ob, cb = "{", "}"
    autocomplete_script = f"""
{function_name}() {ob}
    local cur prev opts
    _init_completion || return
    # complete first argument with script
    if [ $COMP_CWORD -eq 1 ]; then
        opts="{' '.join(output_modules)}"
        COMPREPLY=( $( compgen -W "${ob}opts{cb}" -- "${ob}cur{cb}") )
        return 0
    fi
    # otherwise complete with filesystem
    COMPREPLY=( $(compgen -f -- "${ob}cur{cb}") )
    return 0
{cb}

complete -F {function_name} {command_name}
"""
    return autocomplete_script


def _get_raw_shields_io_output(package: str):
    # todo wrap this request code into a separate function in packg.web
    url = f"https://img.shields.io/pypi/v/{package}"
    logger.info(f"Finding pypi version via {url}")
    counter = 0
    while True:
        try:
            response = requests.get(url, timeout=10)
            break
        except Exception as e:
            logger.warning(f"Error requesting {url}: {format_exception(e)}")
        counter += 1
        time.sleep(1)
    return response.text


_RE_TEXT = re.compile(r"<text.*?>.*?</text>")
_RE_TEXT_VERSION = re.compile(r"<text.*?>v([0-9]+.[0-9]+.[0-9]+)</text>")


def find_pypi_package_version(package: str) -> Optional[str]:
    """
    Find the latest version of a package on pypi.

    pip search was removed. An alternative is to query the shields.io service and parse the
    output svg.
    https://img.shields.io/pypi/v/numpy

    Args:
        package: package name

    Returns:
        version string

    """
    raw = _get_raw_shields_io_output(package)
    # find all occurrences of <text>...</text>
    matches = _RE_TEXT.findall(raw)
    # the last one is the displayed version
    version = matches[-1]
    # find the version number
    match = _RE_TEXT_VERSION.search(version)
    if match:
        version = match.group(1)
        return version
    logger.error(f"Could not find version for {package} on shields.io")
    return None


def main():
    print(_get_raw_shields_io_output("numpy"))


if __name__ == "__main__":
    main()
