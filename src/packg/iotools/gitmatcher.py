"""
Shortcut to create a pathspec from a list of patterns with .gitignore syntax.
"""
from typing import List

import pathspec


def make_git_pathspec(patterns: List[str]) -> pathspec.PathSpec:
    spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)
    return spec


def make_regex_pathspec(patterns: List[str]) -> pathspec.PathSpec:
    spec = pathspec.PathSpec.from_lines(pathspec.RegexPattern, patterns)
    return spec
