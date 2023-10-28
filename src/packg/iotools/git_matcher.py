"""
Shortcut to create a pathspec from a list of patterns with either .gitignore or regex syntax.


"""
from typing import List

import pathspec


def make_git_pathspec(patterns: List[str]) -> pathspec.PathSpec:
    """
    >>> spec1: pathspec.PathSpec = make_git_pathspec(["hello*world"])
    >>> print(spec1.match_file("hello_world"))
    True
    >>> print(spec1.match_file("hello_world.txt"))
    False

    Args:
        patterns:

    Returns:

    """
    spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)
    return spec


def make_regex_pathspec(patterns: List[str]) -> pathspec.PathSpec:
    spec = pathspec.PathSpec.from_lines(pathspec.RegexPattern, patterns)
    return spec
