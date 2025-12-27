"""

Note: Everything inside this directory should not import from this __init__.py file
but from the actual source file. For everything outside, importing from this __init__.py is fine.
"""

from .file_indexer import make_index, regex_glob, sort_file_paths_with_dirs_separated
from .file_reader import (
    open_file_or_io,
    read_bytes_from_file_or_io,
    read_text_from_file_or_io,
    yield_chunked_bytes,
    yield_lines_from_file,
    yield_lines_from_object,
)
from .git_root_finder import find_git_root, navigate_to_git_root
from .jsonext import (
    dump_json,
    dump_json_xz,
    dump_jsonl,
    dumps_json,
    dumps_jsonl,
    load_json,
    load_json_xz,
    load_jsonl,
    loads_json,
    loads_jsonl,
    redump_json,
)
from .misc import (
    format_b_in_gb,
    format_b_in_mb,
    format_bytes_human_readable,
    get_file_size,
    get_file_size_in_mb,
    set_working_directory,
)
from .pathspec_matcher import (
    PathSpecRepr,
    PathSpecWithConversion,
    apply_pathspecs,
    make_and_apply_pathspecs,
    make_git_pathspec,
    make_pathspec,
    make_pathspecs,
    make_regex_pathspec,
)
from .yamlext import dump_yaml, dumps_yaml, load_yaml, loads_yaml

__all__ = [
    "set_working_directory",
    "yield_chunked_bytes",
    "yield_lines_from_file",
    "yield_lines_from_object",
    "load_json",
    "loads_json",
    "load_jsonl",
    "loads_jsonl",
    "dump_json",
    "dumps_json",
    "dump_jsonl",
    "dumps_jsonl",
    "load_json_xz",
    "dump_json_xz",
    "load_yaml",
    "loads_yaml",
    "dump_yaml",
    "dumps_yaml",
    "make_git_pathspec",
    "make_index",
    "find_git_root",
    "navigate_to_git_root",
    "open_file_or_io",
    "read_bytes_from_file_or_io",
    "read_text_from_file_or_io",
    "sort_file_paths_with_dirs_separated",
    "make_regex_pathspec",
    "make_pathspec",
    "PathSpecWithConversion",
    "regex_glob",
    "apply_pathspecs",
    "make_and_apply_pathspecs",
    "make_pathspecs",
    "set_working_directory",
    "get_file_size",
    "get_file_size_in_mb",
    "format_b_in_mb",
    "format_b_in_gb",
    "format_bytes_human_readable",
    "PathSpecRepr",
    "redump_json",
]
