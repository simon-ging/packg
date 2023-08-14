import nbformat
from IPython.display import display
from gutil.iotools.tqdmu import better_tqdm
from importlib_resources import files
from nbconvert import HTMLExporter
from nnt.vis import jnb_static
from packg.strings import quote_with_urlparse
from packg.typext import PathType
from pathlib import Path
from types import ModuleType
from typing import Dict, Any, Union

try:
    from moviepy import editor
except ImportError:
    editor = None

from gutil.iotools.printing import suppress_stdout_stderr
from lxml import html


# ---------- live reloading ----------

def reload_recursive(module, reload_all=False, verbose=False):
    _reload(module, reload_all, set(), verbose=verbose)


def _reload(module, reload_all, reloaded, verbose=False):
    if verbose:
        print(f"trying to reload {module.__name__}")
    if isinstance(module, ModuleType):
        module_name = module.__name__
    elif isinstance(module, str):
        module_name, module = module, import_module(module)
    else:
        raise TypeError(
            "'module' must be either a module or str; "
            f"got: {module.__class__.__name__}")

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        check = (
            # is it a module?
                isinstance(attr, ModuleType) and
                # has it already been reloaded?
                attr.__name__ not in reloaded and
                # is it a proper submodule? (or just reload all)
                (reload_all or attr.__name__.startswith(module_name))
        )
        if check:
            if verbose:
                print(f"recurse into {attr.__name__}")
            _reload(attr, reload_all, reloaded)

    if verbose:
        print(f"reloading module: {module.__name__}")
    reload(module)
    reloaded.add(module_name)
