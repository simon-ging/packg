# packg

<p align="center">
<a href="https://github.com/simon-ging/packg/actions/workflows/build-py37.yml">
  <img alt="build 3.7 status" title="build 3.7 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/packg/build-py37.yml?branch=main&label=python%203.7" />
</a>
<a href="https://github.com/simon-ging/packg/actions/workflows/build-py38.yml">
  <img alt="build 3.8 status" title="build 3.8 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/packg/build-py38.yml?branch=main&label=python%203.8" />
</a>
<a href="https://github.com/simon-ging/packg/actions/workflows/build-py39.yml">
  <img alt="build 3.9 status" title="build 3.9 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/packg/build-py39.yml?branch=main&label=python%203.9" />
</a>
<a href="https://github.com/simon-ging/packg/actions/workflows/build-py310.yml">
  <img alt="build 3.10 status" title="build 3.10 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/packg/build-py310.yml?branch=main&label=python%203.10" />
</a>
<a href="https://github.com/simon-ging/packg/actions/workflows/build-py311.yml">
  <img alt="build 3.11 status" title="build 3.11 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/packg/build-py311.yml?branch=main&label=python%203.11" />
</a>
<a href="https://github.com/simon-ging/packg/actions/workflows/build-py312.yml">
  <img alt="build 3.12 status" title="build 3.12 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/packg/build-py312.yml?branch=main&label=python%203.12" />
</a>
<img alt="coverage" title="coverage" src="https://raw.githubusercontent.com/simon-ging/packg/main/docs/coverage.svg" />
<a href="https://pypi.org/project/packg/">
  <img alt="version" title="version" src="https://img.shields.io/pypi/v/packg?color=success" />
</a>
</p>

Collection of utilities used in other python projects.

## Features

* `caching`: Cache objects to disk (using `joblib`) or to memory
* `constclass.Const`: Base class for defining constants, as alternative to `enum.Enum`
* `debugging`: Connect to PyCharm debug server
* `dtime`: Wrappers and formatters for `datetime` and other timing utilities
* `log`: Wrapper for `loguru`, utilities for stdlib `logging`
* `iotools`: Index paths, compress and read files, git utilities, wrappers to load json/yaml
* `magic`: Wrapper around `importlib`
* `maths`: Various small mathematical utilities
* `misc`: 
  * `format_exception(e)` outputs the exception as it appears in the stacktrace.
  * `suppress_stdout_stderr` context manager to suppress all output of a block of code.
* `multiproc`: Multiprocessing utilities
* `packaging`: Code to handle creation and running of python packages
* `paths`: Load paths from the global environment or .env files using `python-dotenv`
* `stats`: Simple statistics utilities
* `strings`: Base64, quote strings, create random strings, create hashes of objects
* `system`: Wrapper for `subprocess.Popen`
* `testing`: Import all modules from a package and other utilities
* `tqdmext`: Wrapper `tqdm_max_ncols` that limits the width of a `tqdm` progressbar by default
* `typext`: Type definitions
* `web`: Download file and resume a partial download, disable web access 

## Install

Requires `python>=3.7`

```bash
pip install packg
```

## Setup environment paths

```bash
# show environment
python -m packg.cli.show_env

# or
packg show_env

```

To override the defaults with your own values:

- Set the environment variables in your shell e.g. using .bashrc
- Create a file named `.env` in the root of your project as follows:

```bash
ENV_DATA_DIR=data
ENV_RESULT_DIR=results
ENV_ANNO_DIR=annotations
ENV_CODE_DIR=/home/${USER}/code
ENV_CACHE_DIR=/home/${USER}/.cache
```

## Dev install

Clone repository and cd into, then:

~~~bash
pip install -e .
pip install pytest pytest-cov pylint

python -m pytest --cov

pylint packg
pylint tests
~~~
