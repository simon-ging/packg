from __future__ import annotations

import math
import numpy as np
from typing import Iterable, Union


def clip_rectangle_coords(rectangle_coords: tuple[int, int, int, int], w: int, h: int):
    """

    Args:
        rectangle_coords: (x1, y1, x2, y2) of a rectangle
        w: image width
        h: image height

    Returns:
        tuple of rectangle coordinates clipped to image size
    """
    x1, y1, x2, y2 = rectangle_coords
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w - 1, x2)
    y2 = min(h - 1, y2)
    return x1, y1, x2, y2


def round_half_up(x: float) -> int:
    """
    Python/numpy do bankers rounding (round to even). This method rounds 0.5 up to 1 instead.
    """
    return int(math.ceil(x - 0.5))


def round_half_down(x: float) -> int:
    return int(math.floor(x + 0.5))


def np_round_half_up(array: Union[np.ndarray, Iterable[Union[int, float]]]):
    if not isinstance(array, np.ndarray):
        array = np.array(array)
    return np.floor(array + 0.5)


def np_round_half_down(array: Union[np.ndarray, Iterable[Union[int, float]]]):
    if not isinstance(array, np.ndarray):
        array = np.array(array)
    return np.ceil(array - 0.5)


def convert_unsigned_int_to_bytes(int_input: int, length: int = 4) -> bytes:
    """
    convert integer to bytes

    Args:
        int_input:
        length: 4 = int32 (max 4B), 8 = int64 (max 1.9e19)

    Returns:
        bytes
    """
    return int(int_input).to_bytes(length, "big")


def convert_bytes_to_unsigned_int(bytes_input: bytes) -> int:
    """
    convert bytes to integer

    Args:
        bytes_input:

    Returns:
        integer
    """
    if len(bytes_input) == 0:
        raise ValueError("bytes_input must have length > 0 but is empty")
    return int.from_bytes(bytes_input, "big")


def np_str_len(str_arr: Union[np.ndarray, Iterable[str]]) -> np.ndarray:
    """
    Fast way to get string length in a numpy array with datatype string.

    Args:
        str_arr: Numpy array of strings with arbitrary shape.

    Returns:
        Numpy array of string lengths, same shape as input.

    Notes:
        Source: https://stackoverflow.com/questions/44587746/length-of-each-string-in-a-numpy-array
        The latest improved answers don't really work. This code should work for all except strange special characters.
    """
    if not isinstance(str_arr, np.ndarray):
        # also support iterables of strings
        str_arr = np.array(str_arr)
    # check input type
    if str(str_arr.dtype)[:2] != "<U":
        raise TypeError(
            f"Computing string length of dtype {str_arr.dtype} will not work correctly. Cast array to string first."
        )

    # see the link in the docstring as an explanation of what exactly is happening here
    try:
        v = str_arr.view(np.uint32).reshape(str_arr.size, -1)
    except TypeError as e:
        print(f"Input {str_arr} shape {str_arr.shape} dtype {str_arr.dtype}")
        raise e
    len_arr = np.argmin(v, 1)
    len_arr[v[np.arange(len(v)), len_arr] > 0] = v.shape[-1]
    len_arr = np.reshape(len_arr, str_arr.shape)
    return len_arr
