"""
Shortcut to create a pathspec from a list of patterns with either .gitignore or regex syntax.

https://pypi.org/project/pathspec/#description

"""
from pathlib import Path
from typing import Iterable, Union, List, Optional

import pathspec
from attr import define

from packg.typext import PathType
from typedparser import add_argument


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


def make_pathspec(patterns: List[str], regex_mode: bool = False) -> pathspec.PathSpec:
    """
    Create PathSpec object that can be used to match or search files.

    Args:
        patterns: separated list of patterns to search for
        regex_mode: False (default) = .gitignore syntax, True = regex

    Returns:
        PathSpec object
    """
    if regex_mode:
        return make_regex_pathspec(patterns)
    else:
        return make_git_pathspec(patterns)


def apply_specs_to_paths(
    paths: List[PathType],
    include_git: Optional[List[str]] = None,
    include_regex: Optional[List[str]] = None,
    exclude_git: Optional[List[str]] = None,
    exclude_regex: Optional[List[str]] = None,
    gitginore_file: Optional[PathType] = None,
) -> Iterable[Path]:
    if include_git is not None and len(include_git) > 0:
        spec = make_git_pathspec(include_git)
        paths = spec.match_files(paths)
    if include_regex is not None and len(include_regex) > 0:
        spec = make_regex_pathspec(include_regex)
        paths = spec.match_files(paths)
    if exclude_git is not None and len(exclude_git) > 0:
        spec = make_git_pathspec(exclude_git)
        paths = spec.match_files(paths, negate=True)
    if exclude_regex is not None and len(exclude_regex) > 0:
        spec = make_regex_pathspec(exclude_regex)
        paths = spec.match_files(paths, negate=True)
    if gitginore_file is not None:
        spec = make_git_pathspec(gitginore_file.read_text(encoding="utf-8").splitlines())
        paths = spec.match_files(paths, negate=True)
    return paths


@define(slots=False)
class PathSpecArgs:
    exclude_git: List[str] = add_argument(
        shortcut="-x", default=[], action="append", help="Git-like pathspec list to exclude files."
    )
    exclude_regex: List[str] = add_argument(
        shortcut="-X", default=[], action="append", help="Regex pathspec list to exclude files."
    )
    include_git: List[str] = add_argument(
        shortcut="-i", default=[], action="append", help="Git-like pathspec list to include files."
    )
    include_regex: List[str] = add_argument(
        shortcut="-I", default=[], action="append", help="Regex pathspec list to include files."
    )
    gitignore_file: Optional[Path] = add_argument(
        shortcut="-g", type=str, default=None, help="Gitignore file for matching files"
    )


class PathSpecWithConversion:
    """
    Wrapper for pathspec.PathSpec with argument conversion to and from pathlib.Path

    Usage:
        matches = spec.match_tree("path/to/dir")
        matches = spec.match_files(file_paths)
        is_matched = spec.match_file("path/to/file")

    Args:
        patterns: separated list of patterns to search for
        regex_mode: False (default) = .gitignore syntax, True = regex
        output_mode: How to return the matched files. One of "str", "path", "str_posix"
    """

    CONVERTERS = {
        "str": str,
        "path": Path,
        "str_posix": lambda input_path: Path(input_path).as_posix(),
    }

    def __init__(
        self,
        patterns: List[str],
        regex_mode: bool = False,
        input_mode: str = "str",
        output_mode: str = "path",
    ):
        self.patterns = patterns
        self.spec = make_pathspec(patterns, regex_mode=regex_mode)
        self.converter_in = self.CONVERTERS[input_mode]
        self.converter_out = self.CONVERTERS[output_mode]

    def match_tree(self, path: Union[str, Path]) -> Iterable[Path]:
        """Matches all files in path recursively, automatically excludes folders."""
        path = self.converter_in(path)
        for file in self.spec.match_tree(path):
            yield self.converter_out(file)

    def match_files(self, paths: List[Union[str, Path]]) -> Iterable[Path]:
        """Yields all entries in paths that match, does not exclude folders."""
        paths = [self.converter_in(path) for path in paths]
        for file in self.spec.match_files(paths):
            yield self.converter_out(file)

    def match_file(self, path: Union[str, Path]) -> bool:
        """Matches this single path, does not exclude folders."""
        return self.spec.match_file(self.converter_in(path))
