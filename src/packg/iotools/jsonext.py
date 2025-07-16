"""
Wrapper functions for json files.

Behaviour of the JSON writer is changed to:
    - Automatically converts JSON incompatible data types
    (pathlib.Path, numpy arrays, torch tensors, jax tensors) instead of raising errors.
    Paths become strings, tensors become lists.
    - Does not indent each list element as a new line

Possible improvements:
    - Refactor the "file_or_io" handling into a context manager

"""

import math
import sys

import io
import json
import os
from functools import partial
from pathlib import Path
from timeit import default_timer as timer
from typing import Any, Iterable, Sequence, List

from packg import format_exception
from packg.iotools.compress import (
    CompressorC,
    decompress_file_to_str,
    compress_data_to_file,
)
from packg.iotools.file_reader import (
    open_file_or_io,
    read_text_from_file_or_io,
)
from packg.iotools.jsonext_encoder import CustomJSONEncoder
from packg.typext import PathOrIO, PathTypeCls, PathType


def load_json(file_or_io: PathOrIO, verbose: bool = False, encoding: str = "utf-8") -> Any:
    """Load data from json file or file object"""
    start_timer = timer()
    if verbose:
        try:
            file_len = f"{Path(file_or_io).stat().st_size / 1024 ** 2:.1f} MB"
        except Exception:
            try:
                file_len = f"{len(file_or_io) / 1024 ** 2:.1f} M chars"
            except Exception:
                file_len = f"unknown"
        print(f"Load json file {file_or_io} with size {file_len}.")
    data_str = read_text_from_file_or_io(file_or_io, encoding=encoding)
    try:
        obj = loads_json(data_str)
    except Exception as e:
        # # TODO use a general way to reraise the same exception with added information.
        raise RuntimeError(
            f"Probably corrupt json file {file_or_io}",
        ) from e

    if verbose:
        print(f"Loaded json file {file_or_io} in {timer() - start_timer:.3f} seconds")
    return obj


def load_json_compressed(
    file_or_io: PathOrIO,
    compressor_name: CompressorC,
    verbose: bool = False,
    encoding: str = "utf-8",
    **compressor_kwargs,
) -> Any:
    start_timer = timer()
    data_text = decompress_file_to_str(file_or_io, compressor_name, encoding, **compressor_kwargs)
    try:
        obj = loads_json(data_text)
    except Exception as e:
        raise RuntimeError(f"Error loading compressed json file {file_or_io}") from e
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
        raise RuntimeError(f"Error loading jsonl file {file_or_io}") from e
    return data


def load_jsonl_compressed(
    file_or_io: PathOrIO,
    compressor_name: CompressorC,
    verbose: bool = False,
    encoding: str = "utf-8",
    **compressor_kwargs,
) -> Any:
    start_timer = timer()
    data_text = decompress_file_to_str(file_or_io, compressor_name, encoding, **compressor_kwargs)
    try:
        obj = loads_jsonl(data_text)
    except Exception as e:
        raise RuntimeError(f"Error loading compressed jsonl file {file_or_io}") from e
    if verbose:
        print(f"Loaded json file {file_or_io} in {timer() - start_timer:.3f} seconds")
    return obj


def loads_jsonl(s: str) -> List[Any]:
    data = []
    for i, line in enumerate(s.splitlines()):
        try:
            data.append(loads_json(line))
        except Exception as e:
            raise RuntimeError(f"Error loading json line {i}: {line}") from e
    return data


def _check_can_write(file_or_io, overwrite, verbose):
    if not overwrite and isinstance(file_or_io, PathTypeCls) and Path(file_or_io).is_file():
        if verbose:
            print(f"File already exists and overwrite is False: {Path(file_or_io).as_posix()}")
        return False
    return True


def dump_json(
    obj: Any,
    file_or_io: PathOrIO,
    ensure_ascii: bool = False,
    check_circular: bool = False,
    allow_nan=False,
    indent=None,
    separators=None,
    default=None,
    sort_keys=False,
    verbose: bool = True,
    create_parent=False,
    float_precision=None,
    custom_format=True,
    custom_format_nan_to_none=False,
    custom_format_indent_lists=False,
    encoding="utf-8",
    overwrite=True,
) -> None:
    """Write data to json file or file object using the custom json encoder"""
    start_timer = timer()
    if not _check_can_write(file_or_io, overwrite, verbose):
        return

    with open_file_or_io(
        file_or_io, mode="wt", encoding=encoding, create_parent=create_parent
    ) as fh:
        if indent is None and separators is None:
            separators = (",", ":")

        kwargs = dict(
            ensure_ascii=ensure_ascii,
            check_circular=check_circular,
            allow_nan=allow_nan,
            indent=indent,
            separators=separators,
            default=default,
            sort_keys=sort_keys,
        )
        if custom_format:
            kwargs.update(
                dict(
                    cls=CustomJSONEncoder,
                    float_precision=float_precision,
                    custom_format_nan_to_none=custom_format_nan_to_none,
                    custom_format_indent_lists=custom_format_indent_lists,
                )
            )
        try:
            json.dump(obj, fh, **kwargs)
        except KeyboardInterrupt as e:
            if isinstance(fh, (Path, str)):
                print(f"KeyboardInterrupt, removing potentially corrupt json: {fh}")
                Path(fh).unlink()
            raise e

    if verbose:
        print(f"Wrote json file {file_or_io} in {timer() - start_timer:.3f} seconds")


def dump_json_compressed(
    obj: Any,
    file_or_io: PathOrIO,
    compressor_name: CompressorC,
    ensure_ascii: bool = False,
    check_circular: bool = False,
    allow_nan=False,
    indent=None,
    separators=None,
    default=None,
    sort_keys=False,
    verbose: bool = True,
    create_parent=False,
    float_precision=None,
    custom_format=True,
    custom_format_nan_to_none=False,
    custom_format_indent_lists=False,
    encoding="utf-8",
    overwrite=True,
    **compressor_kwargs,
):
    start_timer = timer()
    if not _check_can_write(file_or_io, overwrite, verbose):
        return

    json_data = dumps_json(
        obj,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        indent=indent,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        float_precision=float_precision,
        custom_format=custom_format,
        custom_format_nan_to_none=custom_format_nan_to_none,
        custom_format_indent_lists=custom_format_indent_lists,
    )
    compress_data_to_file(
        json_data,
        file_or_io,
        compressor_name,
        encoding=encoding,
        create_parent=create_parent,
        **compressor_kwargs,
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
    default=None,
    sort_keys=False,
    float_precision=None,
    custom_format=True,
    custom_format_indent_lists=False,
    custom_format_nan_to_none=False,
) -> str:
    """Write data to json string using the custom json encoder"""
    if indent is None and separators is None:
        separators = (",", ":")

    kwargs = dict(
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        indent=indent,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
    )
    if custom_format:
        kwargs.update(
            dict(
                cls=CustomJSONEncoder,
                float_precision=float_precision,
                custom_format_nan_to_none=custom_format_nan_to_none,
                custom_format_indent_lists=custom_format_indent_lists,
            )
        )
    return json.dumps(obj, **kwargs)


def dump_jsonl(
    data: Iterable[Any],
    file_or_io: PathOrIO,
    verbose: bool = True,
    create_parent=False,
    encoding="utf-8",
    overwrite=True,
    ensure_ascii: bool = False,
    check_circular: bool = False,
    allow_nan=False,
    separators=None,
    default=None,
    sort_keys=False,
    float_precision=None,
    custom_format=True,
    custom_format_nan_to_none=False,
) -> None:
    """Write lines of data to jsonl (list of json strings) file or file object"""
    start_timer = timer()
    if not _check_can_write(file_or_io, overwrite, verbose):
        return

    err_msg = f"data must be a list/sequence but is {type(data)}"
    assert not isinstance(data, str), err_msg
    assert isinstance(data, Sequence), err_msg

    with open_file_or_io(file_or_io, "wt", encoding=encoding, create_parent=create_parent) as fh:
        for d in data:
            json_line = dumps_json(
                d,
                ensure_ascii=ensure_ascii,
                check_circular=check_circular,
                allow_nan=allow_nan,
                separators=separators,
                default=default,
                sort_keys=sort_keys,
                float_precision=float_precision,
                custom_format=custom_format,
                custom_format_nan_to_none=custom_format_nan_to_none,
            )
            fh.write(f"{json_line}\n")

    if verbose:
        print(f"Wrote jsonl file {file_or_io} in {timer() - start_timer:.3f} seconds")


def dump_jsonl_compressed(
    data: Iterable[Any],
    file_or_io: PathOrIO,
    compressor_name: CompressorC,
    verbose: bool = True,
    create_parent=False,
    encoding="utf-8",
    overwrite=True,
    ensure_ascii: bool = False,
    check_circular: bool = False,
    allow_nan=False,
    separators=None,
    default=None,
    sort_keys=False,
    float_precision=None,
    custom_format=True,
    custom_format_nan_to_none=False,
    **compressor_kwargs,
) -> None:
    """Write lines of data to jsonl (list of json strings) file or file object
    using the custom json encoder"""
    start_timer = timer()
    if not _check_can_write(file_or_io, overwrite, verbose):
        return

    try:
        jsonl_data = dumps_jsonl(
            data,
            ensure_ascii=ensure_ascii,
            check_circular=check_circular,
            allow_nan=allow_nan,
            separators=separators,
            default=default,
            sort_keys=sort_keys,
            float_precision=float_precision,
            custom_format=custom_format,
            custom_format_nan_to_none=custom_format_nan_to_none,
        )
    except Exception as e:
        raise RuntimeError(f"Error dumping jsonl file {file_or_io}") from e

    compress_data_to_file(
        jsonl_data,
        file_or_io,
        compressor_name,
        encoding=encoding,
        create_parent=create_parent,
        **compressor_kwargs,
    )
    if verbose:
        print(f"Wrote jsonl file {file_or_io} in {timer() - start_timer:.3f} seconds")


def dumps_jsonl(data: Iterable[Any], **kwargs) -> str:
    sio = io.StringIO()
    dump_jsonl(data, sio, verbose=False, **kwargs)
    return sio.getvalue()


load_json_xz = partial(load_json_compressed, compressor_name=CompressorC.LZMA)
dump_json_xz = partial(dump_json_compressed, compressor_name=CompressorC.LZMA)
load_jsonl_xz = partial(load_jsonl_compressed, compressor_name=CompressorC.LZMA)
dump_jsonl_xz = partial(dump_jsonl_compressed, compressor_name=CompressorC.LZMA)

load_json_zst = partial(load_json_compressed, compressor_name=CompressorC.ZSTD)
dump_json_zst = partial(dump_json_compressed, compressor_name=CompressorC.ZSTD)
load_jsonl_zst = partial(load_jsonl_compressed, compressor_name=CompressorC.ZSTD)
dump_jsonl_zst = partial(dump_jsonl_compressed, compressor_name=CompressorC.ZSTD)
