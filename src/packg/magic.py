from importlib import reload, import_module
from types import ModuleType


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
            "'module' must be either a module or str; " f"got: {module.__class__.__name__}"
        )

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        # is it a module, has it already been reloaded, is it a proper submodule or reload_all
        if (
            isinstance(attr, ModuleType)
            and attr.__name__ not in reloaded
            and (reload_all or attr.__name__.startswith(module_name))
        ):
            if verbose:
                print(f"recurse into {attr.__name__}")
            _reload(attr, reload_all, reloaded)

    if verbose:
        print(f"reloading module: {module.__name__}")
    reload(module)
    reloaded.add(module_name)
