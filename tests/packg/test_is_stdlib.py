import sys

import pytest

from packg.testing.import_from_source import get_installed_top_level_packages, is_stdlib


def test_is_stdlib():
    assert is_stdlib("sys", verbose=True) == True
    assert is_stdlib("os", verbose=True) == True
    assert is_stdlib("packg", verbose=True) == False
    assert is_stdlib("attrs", verbose=True) == False


VERBOSE = False
sv = sys.version_info


@pytest.mark.skipif(sv < (3, 10), reason=f"No sys.stdlib_module_names in python version {sv}")
def test_is_stdlib_all():
    for module in sorted(sys.stdlib_module_names):
        is_stdlib_here = is_stdlib(module, verbose=VERBOSE)
        if is_stdlib_here is None:
            print(f"Skipping {module} as we could not determine if it is stdlib")
            continue
        assert is_stdlib_here == True, f"{module} should be stdlib"


@pytest.mark.skipif(sv < (3, 10), reason=f"No sys.stdlib_module_names in python version {sv}")
def test_is_not_stdlib_all():
    toplevel_names = set(get_installed_top_level_packages())
    stdlib_names = set(sys.stdlib_module_names)
    delta = sorted(toplevel_names - stdlib_names)

    for module in delta:
        is_stdlib_here = is_stdlib(module, verbose=VERBOSE)
        if is_stdlib_here is None:
            print(f"Skipping {module} as we could not determine if it is stdlib")
            continue
        assert is_stdlib_here == False, f"{module} should not be stdlib"
