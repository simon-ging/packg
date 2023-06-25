from typing import Optional

import numpy as np
from packg.typext import TensorType


def ensure_numpy(inp: TensorType) -> np.ndarray:
    if isinstance(inp, np.ndarray):
        return inp
    if hasattr(inp, "numpy"):
        return inp.numpy()
    return np.array(inp)


def describe_stats(arr: TensorType,
                   name: str = "",
                   format_str: str = "{:.2f}",
                   table_sep: Optional[str] = None,
                   ) -> str:
    """
    See also lovely-tensors package for things like this

    Args:
        arr: array or tensor
        name: name of the tensor
        format_str: format string for printing
        table_sep: separator for table output (e.g. CSV) or none for human readable output (default)

    """
    arr = ensure_numpy(arr)
    out_strs = []
    if table_sep is not None:
        fmt_str = table_sep.join([format_str] * 5)
        out_strs.append(f"{name}{table_sep}{len(arr)}{table_sep}")
    else:
        fmt_str = ("Range: " + format_str + " to " + format_str + ", mean: " + format_str +
                   ", std: " + format_str + ", median: " + format_str)
        out_strs.append(f"{name}: #{len(arr)}, ")
    out_strs.append(
        fmt_str.format(np.min(arr), np.max(arr), np.mean(arr), np.std(arr), np.median(arr)))
    return "".join(out_strs)
