from __future__ import annotations

import math


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
