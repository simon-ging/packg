"""
Utilities for python packages.

todo split this into multiple, make the get_module... thing faster and depend on less.
thenr eenable the logger.
"""
from __future__ import annotations

import importlib
import os
import re
import requests
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from packg.iotools import sort_file_paths_with_dirs_separated
from packg.misc import format_exception
from packg.strings import create_nested_abbreviations
from packg.testing.import_from_source import recurse_modules


def run_package(main_file, run_dir="cli", recursive=True, run_dir_only=True, abbreviations=True):
    """
    todo remove this. it is too slow and ineffective. solve the problem in bash,
         or use the way simpler approach to import the main function and run it.

    Create a command line interface for a package given a directory of scripts.

    Check the run directory, list scripts, create shortcuts, run if given shortcut.

    Args:
        main_file: __file__ attribute of __main__.py e.g.
            /path/to/lmbtools/python/lmbtools/__main__.py
        run_dir: submodule with run scripts
        recursive: if True, recursively search for scripts
        run_dir_only: if True, only enable running scripts in the run_dir
        abbreviations: if True, create abbreviations for the scripts
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

    abbrevs = None
    if abbreviations:
        abbrevs = create_nested_abbreviations(package_scripts)

    args = sys.argv[1:]
    if len(args) > 0:
        abbrev_arg = args[0]
        if abbrevs is not None and abbrev_arg in abbrevs:
            script = abbrevs[abbrev_arg]
            target = f"{package_name}.{run_dir}.{script}"
            run_script(target, args)
            return

        target = f"{package_name}.{abbrev_arg}"
        if run_dir_only:
            target = f"{package_name}.{run_dir}.{abbrev_arg}"
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

    # no arguments, error, show help
    if abbreviations:
        print(f"Usage option 1: {package_name} shortcut [args]")
        print(f"Usage option 2: {package_name} path.to.module [args]")
        print()
        print(f"shortcut   script")
        for abbrev, f in abbrevs.items():
            if run_dir_only:
                print(f"{abbrev:10s} {f}")
            else:
                print(f"{abbrev:10s} {run_dir}.{f}")
        return

    # show help but without abbreviations
    print(f"Usage: {package_name} path.to.module [args]")
    print()
    print(f"Available scripts:")
    for f in package_scripts:
        if run_dir_only:
            print(f"{f}")
        else:
            print(f"{run_dir}.{f}")


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


def get_modules_for_autocomplete(package: str, run_dir: Optional[str] = None):
    packages_only = set(_recurse_modules_remove_root_package(package, packages_only=True))
    all_modules = set(_recurse_modules_remove_root_package(package))
    output_modules = []

    for m in sorted(all_modules):
        if m in packages_only:
            mlog = f"{package}.{m}"
            if f"{m}.__main__" not in all_modules:
                # print(f"SKIP package: {mlog}")
                continue
            # print(f"ADD package (has __main__): {mlog}")
        if m.endswith("__main__"):
            # print(f"SKIP __main__ file itself: {mlog}")
            continue
        output_modules.append(m)
    output_modules.sort()

    if run_dir is not None:
        new_output_modules = []
        for output_module in output_modules:
            if output_module.startswith(run_dir):
                new_output_modules.append(output_module)
        output_modules = new_output_modules
    return output_modules


def create_bash_autocomplete_script(
    package: str, function_name: str = None, command_name: str = None, run_dir: Optional[str] = None
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
        run_dir: only create autocompletion for this directory

    Returns:

    """
    output_modules = get_modules_for_autocomplete(package, run_dir=run_dir)
    if function_name is None:
        function_name = f"_{package}"
    if command_name is None:
        command_name = package
    ob, cb = "{", "}"
    autocomplete_script = f"""
# source this file to enable autocompletion for {package} command
{function_name}() {ob}
    local cur prev opts
    _init_completion || return
    # complete first argument with script
    if [ $COMP_CWORD -eq 1 ]; then
        opts="{' '.join(output_modules)}"
        COMPREPLY=( $( compgen -W "${ob}opts{cb}" -- "${ob}cur{cb}") )
        return 0
    fi
    # # otherwise complete with filesystem
    # COMPREPLY=( $(compgen -f -- "${ob}cur{cb}") )
    _filedir
    return 0
{cb}

complete -F {function_name} {command_name}
"""
    return autocomplete_script


def create_new_bash_autocomplete_script(
    packages: list[str],
    command_name: str = "py",
    function_name: Optional[str] = None,
    run_dir: Optional[str] = None,
) -> str:
    """
    New version: allinone e.g. alias py and then complete for all installed packages.

    Args:
        packages: packages to create the autocomplete for
        function_name: default _{package}
        command_name: default {package}
        run_dir: only create autocompletion for this directory

    Returns:

    """
    all_output_modules = []
    for package in packages:
        output_modules = get_modules_for_autocomplete(package, run_dir=run_dir)
        output_modules = [f"{package}.{m}" for m in output_modules]
        # logger.debug(f"package={package} output_modules={output_modules}")
        if len(output_modules) == 0:
            print(f"WARN: Nothing found for package {package} in {run_dir}, is it installed?")
        all_output_modules.extend(output_modules)
    if function_name is None:
        function_name = f"_{command_name}"

    ob, cb = "{", "}"
    autocomplete_script = f"""
{function_name}() {ob}
    local cur prev opts
    _init_completion || return
    # complete second argument with script, iff first argument is -m
    if [[ $COMP_CWORD -eq 2 && $prev == "-m" ]]; then
        opts="{' '.join(all_output_modules)}"
        COMPREPLY=( $( compgen -W "${ob}opts{cb}" -- "${ob}cur{cb}") )
        return 0
    fi
    # # otherwise complete with filesystem
    # COMPREPLY=( $(compgen -f -- "${ob}cur{cb}") )
    _filedir
    return 0
{cb}

complete -F {function_name} {command_name}
"""
    return autocomplete_script


FILEDIR_AUTOCOMPLETE = r"""
_filedir()  # source: ubuntu 2004 /usr/share/bash-completion/bash_completion
{
    local IFS=$'\n'
    _tilde "$cur" || return
    local -a toks
    local reset
    if [[ "$1" == -d ]]; then
        reset=$(shopt -po noglob); set -o noglob
        toks=( $(compgen -d -- "$cur") )
        IFS=' '; $reset; IFS=$'\n'
    else
        local quoted
        _quote_readline_by_ref "$cur" quoted
        # Munge xspec to contain uppercase version too
        # http://thread.gmane.org/gmane.comp.shells.bash.bugs/15294/focus=15306
        local xspec=${1:+"!*.@($1|${1^^})"} plusdirs=()
        # Use plusdirs to get dir completions if we have a xspec; if we don't,
        # there's no need, dirs come along with other completions. Don't use
        # plusdirs quite yet if fallback is in use though, in order to not ruin
        # the fallback condition with the "plus" dirs.
        local opts=( -f -X "$xspec" )
        [[ $xspec ]] && plusdirs=(-o plusdirs)
        [[ ${COMP_FILEDIR_FALLBACK-} ]] || opts+=( "${plusdirs[@]}" )
        reset=$(shopt -po noglob); set -o noglob
        toks+=( $(compgen "${opts[@]}" -- $quoted) )
        IFS=' '; $reset; IFS=$'\n'
        # Try without filter if it failed to produce anything and configured to
        [[ -n ${COMP_FILEDIR_FALLBACK:-} && -n "$1" && ${#toks[@]} -lt 1 ]] && {
            reset=$(shopt -po noglob); set -o noglob
            toks+=( $(compgen -f "${plusdirs[@]}" -- $quoted) )
            IFS=' '; $reset; IFS=$'\n'
        }
    fi
    if [[ ${#toks[@]} -ne 0 ]]; then
        # 2>/dev/null for direct invocation, e.g. in the _filedir unit test
        compopt -o filenames 2>/dev/null
        COMPREPLY+=( "${toks[@]}" )
    fi
} # _filedir()

"""


def _get_raw_shields_io_output(package: str):
    # todo wrap this request code into a separate function in packg.web
    url = f"https://img.shields.io/pypi/v/{package}"
    print(f"Finding pypi version via {url}")
    counter = 0
    while True:
        try:
            response = requests.get(url, timeout=10)
            break
        except Exception as e:
            print(f"ERROR requesting {url}: {format_exception(e)}")
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
    print(f"ERROR: Could not find version for {package} on shields.io")
    return None


def find_top_level_package(file_path, verbose: bool = True):
    """
    Args:
        file_path: __file__ of the module or script you want to find the top-level package for
    Returns:
    """
    print_fn = print if verbose else lambda *args, **kwargs: None
    current_file_path = os.path.abspath(file_path)
    print_fn(f"Current file path: {current_file_path}")
    package = __package__
    print_fn(f"__package__: {package}")
    name = __name__
    print_fn(f"__name__: {name}")

    # Attempt to determine the top-level package
    if package:
        top_level_package = package.split(".")[0]
    else:
        # If __package__ is None, infer top-level package from the file structure
        top_level_package = os.path.basename(os.path.dirname(current_file_path))

    print_fn(f"Top-level package: {top_level_package}")
    return top_level_package


def main():
    print(_get_raw_shields_io_output("numpy"))


if __name__ == "__main__":
    main()
