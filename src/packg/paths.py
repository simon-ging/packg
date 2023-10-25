"""
Note: dotenv.load_dotenv doesnt work. Use dotenv_values instead.
todo write a unit test for these functions here

Global path definitions for projects.

Resolution is as follows:

1. Load from environment variables if defined
2. Find and load from .env file in the current directory (see example below)
3. Use the defaults defined here

Usage in python:
    print(get_data_dir())

Usage in yaml with omegaconf:
    storage: ${oc.env:ENV_DATA_DIR}/datasetname

Example .env file content:

ENV_DATA_DIR=data
ENV_RESULT_DIR=results
ENV_ANNO_DIR=annotations
ENV_CODE_DIR=/home/${USER}/code
ENV_CACHE_DIR=/home/${USER}/.cache

"""
import os
from getpass import getuser
from pathlib import Path

from dotenv import dotenv_values, find_dotenv

from packg.constclass import Const
from packg.typext import OptionalPathType


class EnvKeys(Const):
    ENV_DATA_DIR = "ENV_DATA_DIR"  # datasets base directory
    ENV_RESULT_DIR = "ENV_RESULT_DIR"  # results
    ENV_ANNO_DIR = "ENV_ANNO_DIR"  # annotations
    ENV_CODE_DIR = "ENV_CODE_DIR"  # parent directory for the git repositories
    ENV_CACHE_DIR = "ENV_CACHE_DIR"  # cache


uname = getuser()

_DEFAULTS = {
    EnvKeys.ENV_DATA_DIR: "data",
    EnvKeys.ENV_RESULT_DIR: "results",
    EnvKeys.ENV_ANNO_DIR: "annotations",
    EnvKeys.ENV_CODE_DIR: f"/home/{uname}/code",
    EnvKeys.ENV_CACHE_DIR: f"/home/{uname}/.cache",
}

_setup_environ_done = False


def setup_environ(verbose=False, override=True, dotenv_path=None, load_env_file=True):
    global _setup_environ_done
    if _setup_environ_done:
        if verbose:
            print("setup_environ already done")
        return
    _setup_environ_done = True

    if load_env_file:
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
                print(f"Got from env: {values} found it as {find_dotenv()} from {os.getcwd()}")
        else:
            values = {}
            if verbose:
                print(f"Dotenv file not found.")
        for k, v in values.items():
            if override or k not in os.environ:
                if verbose:
                    print(f"From .env write: {k}={v}")
                os.environ[k] = v

    for env_k, v in _DEFAULTS.items():
        if env_k not in os.environ:
            if verbose:
                print(f"From packg.paths defaults write: {env_k}={v}")
            os.environ[env_k] = v


def get_from_environ(env_k: str):
    setup_environ()
    return os.environ[env_k]


def print_all_environment_variables(print_fn=print):
    setup_environ(verbose=True)
    print_fn(f"Path definitions:")
    for env_k in EnvKeys.values():
        print_fn(f"    {env_k}={os.environ[env_k]}")


def get_data_dir(overwrite_dir: OptionalPathType = None) -> Path:
    return get_path_from_env(EnvKeys.ENV_DATA_DIR, overwrite_dir)


def get_result_dir(overwrite_dir: OptionalPathType = None) -> Path:
    return get_path_from_env(EnvKeys.ENV_RESULT_DIR, overwrite_dir)


def get_anno_dir(overwrite_dir: OptionalPathType = None) -> Path:
    return get_path_from_env(EnvKeys.ENV_ANNO_DIR, overwrite_dir)


def get_code_dir(overwrite_dir: OptionalPathType = None) -> Path:
    return get_path_from_env(EnvKeys.ENV_CODE_DIR, overwrite_dir)


def get_cache_dir(overwrite_dir: OptionalPathType = None) -> Path:
    return get_path_from_env(EnvKeys.ENV_CACHE_DIR, overwrite_dir)


def get_path_from_env(env_k: str, overwrite_dir: OptionalPathType = None) -> Path:
    if overwrite_dir is not None:
        return Path(overwrite_dir)
    return Path(get_from_environ(env_k))
