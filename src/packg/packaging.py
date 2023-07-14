"""
Utilities for python packages.
"""
import importlib
import sys
from pathlib import Path

from packg.iotools.misc import sort_file_paths_with_dirs_separated
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
    sorted_scripts = sort_file_paths_with_dirs_separated(
        package_scripts, dirs_first=False
    )
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
        except ModuleNotFoundError:
            found = False

        if found:
            run_script(target, args)
            return
        else:
            print(f"Error, script not found: {abbrev_arg}")

    print(f"Usage option 1: {package_name} shortcut [args]")
    print(f"Usage option 2: {package_name} path.to.module [args]")
    print()
    print(f"shortcut   script")
    for abbrev, f in abbrevs.items():
        print(f"{abbrev:10s} {run_dir}.{f}")


def run_script(target, args):
    print(f"Running {target}")
    module = importlib.import_module(target)
    main = getattr(module, "main")
    sys.argv = [sys.argv[0]] + args[1:]
    main()
