"""
Wrapper functions for json files.

Behaviour of the JSON writer is changed to:
    - Automatically converts JSON incompatible data types to lists
    (pathlib.Path, numpy arrays, torch tensors, jax tensors) instead of raising errors
    - Does not indent each list element as a new line

Possible improvements:
    - Refactor the "file_or_io" handling into a context manager

"""
import io
import json
import lzma
import os
from pathlib import Path
from timeit import default_timer as timer
from typing import Any, Iterable, Sequence, List

from packg.iotools.compressed import load_xz
from packg.iotools.jsonext_encoder import CustomJSONEncoder
from packg.iotools.misc import open_file_or_io, read_text_from_file_or_io
from packg.typext import PathOrIO, PathType


def load_json(
    file_or_io: PathOrIO, verbose: bool = False, encoding: str = "utf-8"
) -> Any:
    """Load data from json file or file object"""
    start_timer = timer()
    data_str = read_text_from_file_or_io(file_or_io, encoding=encoding)
    try:
        obj = loads_json(data_str)
    except Exception as e:
        raise RuntimeError(f"Error loading json file {file_or_io}") from e
    if verbose:
        print(f"Loaded json file {file_or_io} in {timer() - start_timer:.3f} seconds")
    return obj


def loads_json(s: str) -> Any:
    """Load data from json string"""
    return json.loads(s)


def load_jsonl(file_or_io: PathOrIO, encoding: str = "utf-8") -> List[Any]:
    """Load data from jsonl (list of json strings) file or file object.

    Notes:
        This is inefficient for large files. In that case, iterate the file lines
        and use loads_json on each line.
    """
    data_str = read_text_from_file_or_io(file_or_io, encoding=encoding)
    try:
        data = loads_jsonl(data_str)
    except Exception as e:
        raise RuntimeError(
            f"Error loading json file {file_or_io} (see reraised error)"
        ) from e
    return data


def loads_jsonl(s: str) -> List[Any]:
    data = []
    for i, line in enumerate(s.splitlines()):
        try:
            data.append(loads_json(line))
        except Exception as e:
            raise RuntimeError(f"Error loading json line {i}: {line}") from e
    return data


def dump_json(
    obj: Any,
    file_or_io: PathOrIO,
    ensure_ascii: bool = False,
    check_circular: bool = False,
    allow_nan=False,
    indent=None,
    separators=None,
    sort_keys=False,
    verbose: bool = True,
    create_parent=False,
    float_precision=None,
) -> None:
    """Write data to json file or file object using the custom json encoder"""
    start_timer = timer()
    with open_file_or_io(
        file_or_io, "wt", encoding="utf8", create_parent=create_parent
    ) as fh:
        if indent is None and separators is None:
            separators = (",", ":")

        json.dump(
            obj,
            fh,
            cls=CustomJSONEncoder,
            ensure_ascii=ensure_ascii,
            check_circular=check_circular,
            allow_nan=allow_nan,
            indent=indent,
            separators=separators,
            sort_keys=sort_keys,
            float_precision=float_precision,
        )

    if verbose:
        print(f"Wrote json file {file_or_io} in {timer() - start_timer:.3f} seconds")


def dumps_json(
    obj: Any,
    ensure_ascii: bool = False,
    check_circular: bool = False,
    allow_nan=False,
    indent=None,
    separators=None,
    sort_keys=False,
    float_precision=None,
) -> str:
    """Write data to json string using the custom json encoder"""
    return json.dumps(
        obj,
        cls=CustomJSONEncoder,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        indent=indent,
        separators=separators,
        sort_keys=sort_keys,
        float_precision=float_precision,
    )


def dump_jsonl(
    data: Iterable[Any], file_or_io: PathOrIO, verbose: bool = True, create_parent=False
) -> None:
    """Write lines of data to jsonl (list of json strings) file or file object
    using the custom json encoder"""
    start_timer = timer()
    err_msg = f"data must be a list/sequence but is {type(data)}"
    assert not isinstance(data, str), err_msg
    assert isinstance(data, Sequence), err_msg

    with open_file_or_io(
        file_or_io, "wt", encoding="utf8", create_parent=create_parent
    ) as fh:
        for d in data:
            fh.write(f"{dumps_json(d)}\n")

    if verbose:
        print(f"Wrote jsonl file {file_or_io} in {timer() - start_timer:.3f} seconds")


def dumps_jsonl(data: Iterable[Any]) -> str:
    sio = io.StringIO()
    dump_jsonl(data, sio, verbose=False)
    return sio.getvalue()


def load_json_xz(file: PathType, verbose: bool = False, encoding: str = "utf-8") -> Any:
    start_timer = timer()
    file = Path(file)
    data_str = load_xz(file, encoding=encoding)
    try:
        obj = loads_json(data_str)
    except Exception as e:
        raise RuntimeError(f"Error loading json file {file}") from e
    if verbose:
        print(f"Loaded json file {file} in {timer() - start_timer:.3f} seconds")
    return obj


def dump_json_xz(
    obj: Any,
    file: PathType,
    ensure_ascii: bool = False,
    check_circular: bool = False,
    allow_nan=False,
    indent=None,
    separators=None,
    sort_keys=False,
    verbose: bool = True,
    create_parent=False,
    float_precision=None,
) -> None:
    start_timer = timer()
    file = Path(file)
    if create_parent:
        os.makedirs(file.parent, exist_ok=True)
    with lzma.open(file, "wt", encoding="utf8") as fh:
        try:
            dump_json(
                obj,
                fh,
                ensure_ascii=ensure_ascii,
                check_circular=check_circular,
                allow_nan=allow_nan,
                indent=indent,
                separators=separators,
                sort_keys=sort_keys,
                verbose=verbose,
                create_parent=create_parent,
                float_precision=float_precision,
            )
        except Exception as e:
            raise RuntimeError(f"Error dumping json xz file {file}") from e

    if verbose:
        print(f"Wrote json xz file {file} in {timer() - start_timer:.3f} seconds")