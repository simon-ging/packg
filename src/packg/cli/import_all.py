"""
import all installed packages (useful to check for errors, to pre-generate cache etc.)

for i in $(cat import_all.txt); do echo $i; python -c "import $i; print($i.__name__)"; done

"""

from importlib.metadata import entry_points
from pathlib import Path
import tempfile

from packg.iotools import make_git_pathspec
from packg.system import systemcall
from pathlib import Path
from typing import Optional

from loguru import logger
from attrs import define
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.testing import recurse_modules
from packg.tqdmext import tqdm_max_ncols
from typedparser import VerboseQuietArgs, add_argument, TypedParser


@define
class Args(VerboseQuietArgs):
    filter_imports: str = add_argument(shortcut="-f", type=str, help="Filter imports", default="")
    filter_package_list: str = add_argument(
        shortcut="-p", type=str, help="Filter package list", default=""
    )
    recursive: bool = add_argument(
        shortcut="-r", action="store_true", help="Recursively import all"
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    eps = entry_points()
    all_vs = []
    for k, vs in eps.items():
        for v in vs:
            all_vs.append(v.value.split(":")[0])
    all_vs = sorted(set(all_vs))
    more_vs = []
    spec = None
    if len(args.filter_imports) > 0:
        filter_list = args.filter_imports.split(",")
        spec = make_git_pathspec(filter_list)
    filter_package_set = set()
    if len(args.filter_package_list) > 0:
        filter_package_set = set(args.filter_package_list.split(","))
    for v in all_vs:
        current = []
        for part in v.split("."):
            current.append(part)
            to_add = ".".join(current)
            if spec is not None and not spec.match_file(to_add):
                continue
            if len(filter_package_set) > 0 and to_add not in filter_package_set:
                continue
            more_vs.append(to_add)
    more_vs = sorted(set(more_vs))
    with tempfile.NamedTemporaryFile(
        prefix="python_import_all_file", suffix=".txt", delete=True, mode="wt", encoding="utf-8"
    ) as fh:
        print(f"Wrote: {fh.name}")
        fh.write("\n".join(more_vs))
        fh.flush()

    all_module_dict = {}
    for v in more_vs:
        module_list = [v]
        if args.recursive:
            module_list += list(recurse_modules(v, ignore_tests=True, packages_only=False))
        all_module_dict[v] = module_list
    total_len = sum(len(v) for v in all_module_dict.values())

    pbar = tqdm_max_ncols(desc="Importing", total=total_len)
    for v, module_list in all_module_dict.items():
        pbar.write(f"---------- importing {v} len {len(module_list)} total {total_len} ----------")
        strs = []
        for mod in module_list:
            strs += [
                "try:",
                f"    import {mod}",
                f"    print(\"{mod}\", end=\" \", flush=True)",
                "except Exception as e:",
                f"    from packg import format_exception",
                f"    print(f\"Error importing {mod}\")",
                f"    print(format_exception(e))",
                f"    print()",
                f""
            ]
        final_str = "\n".join(strs)
        out, err, retcode = systemcall(f"python -c '{final_str}'")
        outputs = []
        if retcode != 0:
            outputs.append(f"ERROR CODE: {retcode}")
        if out.strip() != "":
            outputs.append(out.strip())
        if err.strip() != "":
            outputs.append(err.strip())
        if len(outputs) > 0:
            pbar.write("\n".join(outputs))
        pbar.update(len(module_list))


if __name__ == "__main__":
    main()
