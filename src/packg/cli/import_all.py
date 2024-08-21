"""
import all installed packages (useful to check for errors, to pre-generate cache etc.)

for i in $(cat import_all.txt); do echo $i; python -c "import $i; print($i.__name__)"; done

"""

from importlib.metadata import entry_points
from pathlib import Path
import tempfile

from packg.system import systemcall


def main():
    eps = entry_points()
    all_vs = []
    for k, vs in eps.items():
        for v in vs:
            all_vs.append(v.value.split(":")[0])
    all_vs = sorted(set(all_vs))
    more_vs = []
    for v in all_vs:
        current = []
        for part in v.split("."):
            current.append(part)
            more_vs.append(".".join(current))
    more_vs = sorted(set(more_vs))
    with tempfile.NamedTemporaryFile(
        prefix="python_import_all_file", suffix=".txt", delete=True, mode="wt", encoding="utf-8"
    ) as fh:
        print(f"Wrote: {fh.name}")
        fh.write("\n".join(more_vs))
        fh.flush()

    for v in more_vs:
        print(f"---------- importing {v}")
        out,err,retcode=systemcall(f"python -c 'import {v}; print({v}.__name__)'")
        if retcode != 0:
            print(F"ERROR CODE: {retcode}")
        if out.strip() != "":
            print(out.strip())
        if err.strip() != "":
            print(err.strip())
        print()


if __name__ == "__main__":
    main()
