"""JSON encoder implementation for jsonext.py"""
# pylint: skip-file
import json
from json.encoder import (
    c_make_encoder,  # noqa
    encode_basestring_ascii,  # noqa
    encode_basestring,  # noqa
    INFINITY,
)
from pathlib import Path

import attrs

from typedparser import NamedTupleMixin


class CustomJSONEncoder(json.JSONEncoder):
    def __init__(  # noqa
        self,
        *,
        skipkeys=False,
        ensure_ascii=False,
        check_circular=True,
        allow_nan=False,
        sort_keys=False,
        indent=None,
        separators=None,
        default=None,
        float_precision=None,
    ):
        self.skipkeys = skipkeys
        self.ensure_ascii = ensure_ascii
        self.check_circular = check_circular
        self.allow_nan = allow_nan
        self.sort_keys = sort_keys
        self.indent = indent
        self.float_precision = float_precision
        if separators is not None:
            self.item_separator, self.key_separator = separators
        # change: do not modify indent here
        if default is not None:
            self.default = default

    def default(self, o):
        # change: added more supported types.
        # note: intentionally checks for jax/torch tensors without importing these packages
        if isinstance(o, Path):
            return o.as_posix()
        full_name = f"{o.__class__.__module__}.{o.__class__.__name__}"
        # if isinstance(o, (np.int8, np.int16, np.int32, np.int64)):
        if full_name in {"numpy.int8", "numpy.int16", "numpy.int32", "numpy.int64"}:
            return int(o)
        # if isinstance(o, (np.float16, np.float32, np.float64)):
        if full_name in {"numpy.float16", "numpy.float32", "numpy.float64"}:
            return float(o)
        # if isinstance(o, np.ndarray):
        if full_name == "numpy.ndarray":
            return o.tolist()
        if hasattr(o, "detach"):  # torch
            return o.detach().cpu().numpy().tolist()
        # todo update below to use full name check once we have a jax example
        class_name = o.__class__.__name__
        if class_name.lower() == "devicearray":  # jax
            return o.tolist()
        if isinstance(o, NamedTupleMixin):
            return attrs.asdict(o)
        raise TypeError(f"Object of type {class_name} is not JSON serializable")

    def iterencode(self, o, _one_shot=False):
        # change: custom iterencode function called
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring

        def floatstr(
            obj,
            allow_nan=self.allow_nan,
            _repr=float.__repr__,
            _inf=INFINITY,
            _neginf=-INFINITY,
        ):
            if obj != obj:
                text = "NaN"
            elif obj == _inf:
                text = "Infinity"
            elif obj == _neginf:
                text = "-Infinity"
            elif self.float_precision is not None:
                return f"{obj:.{self.float_precision}f}"
            else:
                return _repr(obj)  # noqa
            if not allow_nan:
                raise ValueError("Out of range float values are not JSON compliant: " + repr(obj))

            return text

        if (
            _one_shot
            and c_make_encoder is not None
            and self.indent is None
            and self.float_precision is None
        ):
            # only call the original c encoder if available and no custom iterencode logic is needed
            _iterencode = c_make_encoder(
                markers,
                self.default,
                _encoder,
                self.indent,
                self.key_separator,
                self.item_separator,
                self.sort_keys,
                self.skipkeys,
                self.allow_nan,
            )
        else:
            _iterencode = _make_custom_iterencode(
                markers,
                self.default,
                _encoder,
                self.indent,
                floatstr,
                self.key_separator,
                self.item_separator,
                self.sort_keys,
                self.skipkeys,
                _one_shot,
            )
        return _iterencode(o, 0)


def _make_custom_iterencode(
    markers,
    _default,
    _encoder,
    _indent,
    _floatstr,
    _key_separator,
    _item_separator,
    _sort_keys,
    _skipkeys,
    _one_shot,
    # HACK: hand-optimized bytecode; turn globals into locals
    ValueError=ValueError,  # noqa
    dict=dict,  # noqa
    float=float,  # noqa
    id=id,  # noqa
    int=int,  # noqa
    isinstance=isinstance,  # noqa
    list=list,  # noqa
    str=str,  # noqa
    tuple=tuple,  # noqa
    _intstr=int.__repr__,
    indent_list: bool = False,
):
    if _indent is not None and not isinstance(_indent, str):
        _indent = " " * _indent

    # change: no spaces at the end of lines
    _item_separator_eol = _item_separator.rstrip()

    def _iterencode_list(lst, _current_indent_level):
        if not lst:
            yield "[]"
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = "["
        # # change: use indent_list flag, use eol separator
        if _indent is not None and indent_list:
            _current_indent_level += 1
            newline_indent = "\n" + _indent * _current_indent_level
            separator = _item_separator_eol + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = _item_separator
        first = True
        for value in lst:
            if first:
                first = False
            else:
                buf = separator
            if isinstance(value, str):
                yield buf + _encoder(value)
            elif value is None:
                yield buf + "null"
            elif value is True:
                yield buf + "true"
            elif value is False:
                yield buf + "false"
            elif isinstance(value, int):
                # Subclasses of int/float may override __repr__, but we still
                # want to encode them as integers/floats in JSON. One example
                # within the standard library is IntEnum.
                yield buf + _intstr(value)  # noqa
            elif isinstance(value, float):
                # see comment above for int
                yield buf + _floatstr(value)
            else:
                yield buf
                if isinstance(value, (list, tuple)):
                    chunks = _iterencode_list(value, _current_indent_level)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, _current_indent_level)
                else:
                    chunks = _iterencode(value, _current_indent_level)
                yield from chunks
        if newline_indent is not None:
            _current_indent_level -= 1
            yield "\n" + _indent * _current_indent_level
        yield "]"
        if markers is not None:
            del markers[markerid]  # noqa

    def _iterencode_dict(dct, _current_indent_level):
        if not dct:
            yield "{}"
            return
        if markers is not None:
            markerid = id(dct)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield "{"
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = "\n" + _indent * _current_indent_level
            item_separator = _item_separator_eol + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator
        first = True
        if _sort_keys:
            items = sorted(dct.items())
        else:
            items = dct.items()
        for key, value in items:
            if isinstance(key, str):
                pass
            # JavaScript is weakly typed for these, so it makes sense to
            # also allow them.  Many encoders seem to do something like this.
            elif isinstance(key, float):
                # see comment for int/float in _make_iterencode
                key = _floatstr(key)
            elif key is True:
                key = "true"
            elif key is False:
                key = "false"
            elif key is None:
                key = "null"
            elif isinstance(key, int):
                # see comment for int/float in _make_iterencode
                key = _intstr(key)  # noqa
            elif _skipkeys:
                continue
            else:
                raise TypeError(
                    f"keys must be str, int, float, bool or None, " f"not {key.__class__.__name__}"
                )
            if first:
                first = False
            else:
                yield item_separator
            yield _encoder(key)
            yield _key_separator
            if isinstance(value, str):
                yield _encoder(value)
            elif value is None:
                yield "null"
            elif value is True:
                yield "true"
            elif value is False:
                yield "false"
            elif isinstance(value, int):
                # see comment for int/float in _make_iterencode
                yield _intstr(value)  # noqa
            elif isinstance(value, float):
                # see comment for int/float in _make_iterencode
                yield _floatstr(value)
            else:
                if isinstance(value, (list, tuple)):
                    chunks = _iterencode_list(value, _current_indent_level)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, _current_indent_level)
                else:
                    chunks = _iterencode(value, _current_indent_level)
                yield from chunks
        if newline_indent is not None:
            _current_indent_level -= 1
            yield "\n" + _indent * _current_indent_level
        yield "}"
        if markers is not None:
            del markers[markerid]  # noqa

    def _iterencode(o, _current_indent_level):
        if isinstance(o, str):
            yield _encoder(o)
        elif o is None:
            yield "null"
        elif o is True:
            yield "true"
        elif o is False:
            yield "false"
        elif isinstance(o, int):
            # see comment for int/float in _make_iterencode
            yield _intstr(o)  # noqa
        elif isinstance(o, float):
            # see comment for int/float in _make_iterencode
            yield _floatstr(o)
        elif isinstance(o, (list, tuple)):
            yield from _iterencode_list(o, _current_indent_level)
        elif isinstance(o, dict):
            yield from _iterencode_dict(o, _current_indent_level)
        else:
            if markers is not None:
                markerid = id(o)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = o
            o = _default(o)
            yield from _iterencode(o, _current_indent_level)
            if markers is not None:
                del markers[markerid]  # noqa

    return _iterencode
