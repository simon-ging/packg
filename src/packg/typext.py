"""Type extensions"""
from io import IOBase
from pathlib import Path
from typing import Union, Any

from importlib_resources.abc import Traversable

TensorType = Any
PathType = Union[str, Path, Traversable]
OptionalPathType = Union[str, Path, Traversable, None]
PathOrIO = Union[PathType, IOBase]

# Subscripted generics cannot be used with class and instance check
# i.e. to use isinstance(obj, the_type) they need to be defined as a tuple
PathTypeCls = (str, Path, Traversable)
PathOrIOCls = (str, Path, Traversable, IOBase)

try:
    from types import NoneType  # pylint: disable=unused-import
except ImportError:
    NoneType = type(None)
