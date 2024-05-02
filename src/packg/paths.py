"""
Global path definitions for projects.

Resolution is as follows:
1. Load from environment variables if defined
2. Find and load from .env file in the current directory using python dotenv library
3. Use the defaults defined here

Usage in python:
    print(get_data_dir())

Usage in yaml with omegaconf:
    storage: ${oc.env:ENV_DATA_DIR}/datasetname
"""
import os
from dotenv import dotenv_values, find_dotenv
from pathlib import Path

from packg.constclass import Const

HELP_STR = """Solutions:
1. Set the environment variable in the system.
2. Create .env file in the current dir, a parent dir or user home dir and define the variable there. 
3. Change defaults in packg.paths module
"""


class EnvKeys(Const):
    ENV_DATA_DIR = "ENV_DATA_DIR"
    ENV_CACHE_DIR = "ENV_CACHE_DIR"


home = Path.home()

ENV_DEFAULTS = {
    EnvKeys.ENV_DATA_DIR: "data",  # datasets base directory, default is relative dir 'data'
    EnvKeys.ENV_CACHE_DIR: (home / ".cache").as_posix(),
}

_setup_environ_done = False


def setup_environ(
    verbose=False, load_dotenv=True, override_from_dotenv=True, dotenv_path=None, use_defaults=True
):
    global _setup_environ_done
    if _setup_environ_done and not verbose:
        return
    _setup_environ_done = True

    if load_dotenv:
        if dotenv_path is not None:
            dotenv_path = Path(dotenv_path).as_posix()
            if not Path(dotenv_path).is_file():
                raise FileNotFoundError(f"dotenv_path provided but not found: {dotenv_path}")
        else:
            dotenv_path = ""
            if verbose:
                print(f"Searching dotenv file...")

        if dotenv_path == "":
            # try to find it relative to the current dir
            dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path == "":
            # try to find in home
            proposal = Path.home() / ".env"
            if proposal.is_file():
                dotenv_path = proposal.as_posix()

        if dotenv_path != "":
            values = dotenv_values(dotenv_path, verbose=verbose)
            if verbose:
                print(
                    f"Got {len(values)} from .env file, "
                    f"found it as {find_dotenv()} from {os.getcwd()}"
                )
        else:
            values = {}
            if verbose:
                print(f"Dotenv file not found.")
        for k, v in values.items():
            if override_from_dotenv or k not in os.environ:
                if verbose:
                    print(f"    From .env write: {k}={type(v).__name__} length {len(v)}")
                os.environ[k] = v

    if use_defaults:
        for env_k, v in ENV_DEFAULTS.items():
            if env_k not in os.environ:
                if verbose:
                    print(f"from packg.paths defaults write: {env_k}={v}")
                os.environ[env_k] = v


def get_from_environ(env_k: str):
    setup_environ()
    value = os.environ[env_k]
    if value == "" or value is None:
        raise ValueError(f"Environment variable {env_k} is undefined: '{value}'")
    return value


def print_all_environment_variables(print_fn=print):
    setup_environ(verbose=True)
    print_fn(f"Path definitions:")
    for env_k in EnvKeys.values():
        print_fn(f"    {env_k}={os.environ[env_k]}")


def get_data_dir() -> Path:
    return get_path_from_env(EnvKeys.ENV_DATA_DIR)


def get_cache_dir() -> Path:
    return get_path_from_env(EnvKeys.ENV_CACHE_DIR)


def get_path_from_env(env_k: str) -> Path:
    return Path(get_from_environ(env_k))
