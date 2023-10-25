"""
Load and save numpy arrays to bytes and strings.

Note: To get all-in-one
    buffer = io.BytesIO()
    np.save(buffer, score_list)
    arr_bytes = buffer.getvalue()
    buffer = io.BytesIO(cached_score_list)
    score_list = np.load(buffer)
"""

from typing import Tuple

import numpy as np


def dumps_numpy_array(arr) -> Tuple[bytes, str]:
    """
    Convert numpy array into a tuple of bytes and a string describing dtype and shape.
    Useful for then storing it in a database.
    Especially for very small arrays, this method takes much less space then
    np.save or joblib.dump.

    Args:
        arr: Input array

    Returns: tuple of
        bytes: array data as bytes
        str: dtype and shape as string e.g. "float32-100,100" for a 100x100 float32 array

    """
    return arr.tobytes(), f"{arr.dtype.name}-{','.join(str(d) for d in arr.shape)}"


def loads_numpy_array(arr, dtype_shape) -> np.ndarray:
    dtype, shape = dtype_shape.split("-")
    return np.frombuffer(arr, dtype=dtype).reshape([int(s) for s in shape.split(",")])
