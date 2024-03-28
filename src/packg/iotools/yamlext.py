"""
Wrapper functions for YAML I/O.
"""
import difflib
import os
import sys
from collections import abc
from pathlib import Path
from typing import Any

import yaml
from typedparser.objects import is_any_mapping, is_any_iterable, compare_nested_objects,\
    modify_nested_object

from packg.iotools.file_reader import read_text_from_file_or_io
from packg.typext import PathOrIO, PathTypeCls


def load_yaml(file_or_io: PathOrIO) -> Any:
    yaml_str = read_text_from_file_or_io(file_or_io)
    return loads_yaml(yaml_str)


def loads_yaml(yaml_str: str) -> Any:
    return yaml.load(yaml_str, Loader=yaml.SafeLoader)


def dump_yaml(
    obj: Any,
    file_or_io: PathOrIO,
    standard_format: bool = True,
    check_roundtrip: bool = True,
    create_parent=False,
    **kwargs,
) -> None:
    """
    convert python object to yaml string and write to file. see dumps_yaml for details.
    """
    s = dumps_yaml(obj, standard_format=standard_format, check_roundtrip=check_roundtrip, **kwargs)
    if isinstance(file_or_io, PathTypeCls):
        if create_parent:
            os.makedirs(Path(file_or_io).parent, exist_ok=True)
        Path(file_or_io).write_text(s, encoding="utf8")
        return
    file_or_io.write(s)


def _path_to_str_if_path(x):
    if isinstance(x, Path):
        return x.as_posix()
    return x


def dumps_yaml(
    obj: Any, standard_format: bool = True, check_roundtrip: bool = True, **kwargs
) -> str:
    """
    convert python object to yaml string

    Args:
        obj:
        standard_format:
            if True, use the standard yaml format
                (multi-line lists and dicts, default 2 space indents).
            if False, uses custom format (compatible with the standard format):
                - lists and dicts inside those lists are put on a single line
                - default 4 space indents indents of 2
                - strings are put in quotes
                - keys are not sorted by default, but the order is kept
        check_roundtrip: if True, check that the object can be reconstructed from the yaml string.
            this will cost performance if the object is very large.
        **kwargs: passed to yaml dumper if standard_format is True

    Returns:
        yaml string
    """
    if is_any_mapping(obj):
        # yaml does not understand pathlib.Path so first of all convert all paths to str
        obj = modify_nested_object(obj, _path_to_str_if_path, return_copy=True)
    if standard_format:
        return yaml.dump(obj, Dumper=yaml.SafeDumper, **kwargs)
    yaml_str = _dumps_yaml_recursive(obj, **kwargs)
    if check_roundtrip:
        re_obj = loads_yaml(yaml_str)

        if re_obj != obj:
            print(f"---------- Original object:\n{obj}\n", file=sys.stderr)
            print(f"---------- Reconstructed object:\n{re_obj}\n", file=sys.stderr)
            diffs = compare_nested_objects(obj, re_obj)
            diff_str = "\n".join(diffs)
            print(f"---------- Diffs:\n{diff_str}\n", file=sys.stderr)
            raise RuntimeError(
                "roundtrip failed (original object cannot be reconstructed from yaml, see stderr)"
            )
    return yaml_str


def _dumps_yaml_recursive(
    obj: Any, indent: int = 4, _indent_level: int = 0, _is_inside_list: bool = False
) -> str:
    """
    Modified version of yaml.dump with abbreviated lists and dicts.
    """
    # setup key-value collector and indent level
    indent = " " * (_indent_level * indent)

    # check type
    if isinstance(obj, (bool, int, float, type(None))):
        # by yaml standard, if there is only a single objects in the file, append "..." (eod)
        return _convert_single_object_to_yaml_str(
            obj, remove_eod=_indent_level > 0 or _is_inside_list
        )
    if isinstance(obj, str):
        # put quotes around strings
        return f'"{obj}"'
    if is_any_mapping(obj):
        if _is_inside_list:
            # short: dicts inside lists will be kept in the abbreviated form: {key: "value"}
            if len(obj) == 0:
                return "{}"
            dct_strs = ["{"]
            for sub_key, sub_val in obj.items():
                dct_strs.append(
                    f"{sub_key}: " f"{_dumps_yaml_recursive(sub_val, _is_inside_list=True)}"
                )
                dct_strs.append(", ")
            dct_strs.pop()
            dct_strs.append("}")
            return "".join(dct_strs)
        # long: build the dict line by line
        ret_list = []
        for k, v in obj.items():
            kv_sep = "\n" if isinstance(v, abc.Mapping) else " "
            recursive_result = _dumps_yaml_recursive(
                v, _indent_level=_indent_level + 1, _is_inside_list=_is_inside_list
            )
            ret_list.append(f"{indent}{k}:{kv_sep}{recursive_result}")
        return "\n".join(ret_list)
    if is_any_iterable(obj):
        # iterate lists
        return f"[{', '.join((_dumps_yaml_recursive(v, _is_inside_list=True) for v in obj))}]"
    raise ValueError(f"dict to yaml, value type not understood: type={type(obj)} value={obj}")


def _convert_single_object_to_yaml_str(obj, remove_eod: bool = True):
    yaml_str = yaml.dump(obj, Dumper=yaml.SafeDumper, default_flow_style=True)
    if remove_eod:
        # yaml appends "..." (end of document) to the end of the string, remove
        yaml_str = yaml_str.split("...")[0].strip()
    return yaml_str
