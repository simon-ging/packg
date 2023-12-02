# packg

<p align="center">
<a href="https://github.com/gingsi/packg/actions/workflows/build-py37.yml">
  <img alt="build 3.7 status" title="build 3.7 status" src="https://img.shields.io/github/actions/workflow/status/gingsi/packg/build-py37.yml?branch=main&label=build%203.7" />
</a>
<a href="https://github.com/gingsi/packg/actions/workflows/build-py310.yml">
  <img alt="build 3.10 status" title="build 3.10 status" src="https://img.shields.io/github/actions/workflow/status/gingsi/packg/build-py310.yml?branch=main&label=build%203.10" />
</a>
<img alt="coverage" title="coverage" src="https://raw.githubusercontent.com/gingsi/packg/main/docs/coverage.svg" />
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
* `misc`: `format_exception(e)` output the exception as it appears in the stacktrace
* `multiproc`: Multiprocessing utilities
* `packaging`: Code to handle creation and running of python packages
* `paths`: Load paths from the global environment or .env files using `python-dotenv`
* `stats`: Simple utilities for numpy arrays
* `strings`: Base64, quote strings, create random strings
* `system`: Wrapper for `subprocess.Popen`
* `testing`: Import all modules from a package
* `tqdmu`: Wrapper for `tqdm` that limits the width by default
* `typext`: Type definitions
* `web`: Download file and resume a partial download, disable the web access 

## Install

Requires `python>=3.7`

```bash
pip install packg
```

## Setup environment paths

```bash
# show environment
python -m packg.run.show_env
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
pip install pytest pytest-cov pylint pytest-lazy-fixture

python -m pytest --cov

pylint packg
pylint tests
~~~
