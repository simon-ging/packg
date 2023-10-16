import numpy as np
from packg.typext import TensorType


def ensure_numpy(inp: TensorType) -> np.ndarray:
    if isinstance(inp, np.ndarray):
        return inp
    if hasattr(inp, "numpy"):
        return inp.numpy()
    return np.array(inp)


