"""
Global path definitions for projects.

Resolution is as follows:
1. Load from environment variables if defined
2. Use the defaults defined here

Usage in python:
    print(get_data_dir())

Usage in yaml with omegaconf:
    storage: datasetname
"""

import os
from pathlib import Path

from platformdirs import user_cache_path

from packg.constclass import Const


class EnvKeys(Const):
    PACKG_DATA_DIR = "PACKG_DATA_DIR"
    PACKG_CACHE_DIR = "PACKG_CACHE_DIR"


home = Path.home()

ENV_DEFAULTS = {
    EnvKeys.PACKG_DATA_DIR: "data",  # datasets base directory, default is relative dir 'data'
    EnvKeys.PACKG_CACHE_DIR: (user_cache_path("python_packg") / "cache").as_posix(),
}


def get_packg_data_dir() -> Path:
    return get_path_from_env(EnvKeys.PACKG_DATA_DIR)


def get_packg_cache_dir() -> Path:
    return get_path_from_env(EnvKeys.PACKG_CACHE_DIR)


def get_path_from_env(env_k: str) -> Path:
    return Path(get_from_environ(env_k))


def get_from_environ(env_k: str, use_default: bool = True):
    value = os.environ.get(env_k)
    if value is not None:
        return value
    if not use_default:
        raise ValueError(f"Environment variable {env_k} is undefined")
    value = ENV_DEFAULTS.get(env_k)
    if value is not None:
        return value
    raise ValueError(
        f"Environment variable {env_k} is undefined and does not have a default value set. "
        f"Default values exist for: {tuple(ENV_DEFAULTS.keys())}"
    )


def print_all_environment_variables(print_fn=print):
    print_fn(f"Path definitions:")
    for env_k in EnvKeys.values():
        print_fn(f"    {env_k}={os.environ[env_k]}")
