"""
Python Multiprocessing utilities (all non-pytorch / not framework-related).
"""

import abc
import ctypes
import logging
import multiprocessing
import time
import traceback
from dataclasses import dataclass
from queue import Empty
from timeit import default_timer as timer
from typing import List

import numpy as np
import tqdm

from packg.tqdmext import TQDM_WID

MAP_TYPES = {
    "int": ctypes.c_int,
    "long": ctypes.c_long,
    "float": ctypes.c_float,
    "double": ctypes.c_double,
}


def create_shared_array(arr: np.ndarray, dtype: str):
    """Converts an existing numpy array into a shared numpy array, such that
    this array can be used by multiple CPUs. Used e.g. for preloading the
    entire feature dataset into memory and then making it available to multiple
    dataloaders.

    Args:
        arr (np.ndarray): Array to be converted to shared array
        dtype (np.dtype): Datatype of shared array

    Returns:
        shared_array (multiprocessing.Array): shared array
    """
    shape = arr.shape
    flat_shape = int(np.prod(shape))
    c_type = MAP_TYPES[dtype]
    shared_array_base = multiprocessing.Array(c_type, flat_shape)
    shared_array = np.ctypeslib.as_array(shared_array_base.get_obj())
    shared_array = shared_array.reshape(shape)
    shared_array[:] = arr[:]
    return shared_array
