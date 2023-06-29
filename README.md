# packg

<p align="center">
<a href="https://github.com/gingsi/packg/actions/workflows/build_py37.yml">
  <img alt="build 3.7 status" title="build 3.7 status" src="https://img.shields.io/github/actions/workflow/status/gingsi/packg/build_py37.yml?branch=main&label=build%203.7" />
</a>
<a href="https://github.com/gingsi/packg/actions/workflows/build_py39.yml">
  <img alt="build 3.9 status" title="build 3.9 status" src="https://img.shields.io/github/actions/workflow/status/gingsi/packg/build_py39.yml?branch=main&label=build%203.9" />
</a>
<img alt="coverage" title="coverage" src="https://raw.githubusercontent.com/gingsi/packg/main/docs/coverage.svg" />
<a href="https://pypi.org/project/packg/">
  <img alt="version" title="version" src="https://img.shields.io/pypi/v/packg?color=success" />
</a>
</p>

Collection of utilities used in other python projects. 

## Features

* `caching`: Cache objects to disk / to memory
* `Const`: Base class for defining constants, as alternative to `enum.Enum` 
* `typext`: Type definitions
* etc

## Install

Requires `python>=3.7`

```bash
pip install packg
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
