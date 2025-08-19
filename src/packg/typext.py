"""Type extensions"""

from io import IOBase
from pathlib import Path
from typing import Any, Union

TensorType = Any
PathType = Union[str, Path]
OptionalPathType = Union[str, Path, None]
PathOrIO = Union[PathType, IOBase]

# Subscripted generics cannot be used with class and instance check
# i.e. to use isinstance(obj, the_type) they need to be defined as a tuple
PathTypeCls = (str, Path)
PathOrIOCls = (str, Path, IOBase)

try:
    from types import NoneType  # pylint: disable=unused-import
except ImportError:
    NoneType = type(None)
