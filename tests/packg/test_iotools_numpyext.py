import numpy as np

from packg.iotools.numpyext import dumps_numpy_array, loads_numpy_array


def test_dumps_loads_numpy_array():
    # Test with different array types and shapes
    test_cases = [
        np.array([1, 2, 3], dtype=np.int32),
        np.array([[1, 2], [3, 4]], dtype=np.float32),
        np.zeros((3, 4, 5), dtype=np.float64),
        np.ones((2, 2), dtype=np.int64),
        np.random.rand(10, 10).astype(np.float32),
    ]

    for arr in test_cases:
        # Test dumps
        arr_bytes, dtype_shape = dumps_numpy_array(arr)
        assert isinstance(arr_bytes, bytes)
        assert isinstance(dtype_shape, str)
        assert arr.dtype.name in dtype_shape
        assert all(str(d) in dtype_shape for d in arr.shape)

        # Test loads
        reconstructed = loads_numpy_array(arr_bytes, dtype_shape)
        assert isinstance(reconstructed, np.ndarray)
        assert reconstructed.dtype == arr.dtype
        assert reconstructed.shape == arr.shape
        np.testing.assert_array_equal(reconstructed, arr)


def test_dumps_loads_numpy_array_edge_cases():
    # Test empty array
    empty_arr = np.array([], dtype=np.float32)
    arr_bytes, dtype_shape = dumps_numpy_array(empty_arr)
    reconstructed = loads_numpy_array(arr_bytes, dtype_shape)
    assert reconstructed.size == 0
    assert reconstructed.dtype == empty_arr.dtype

    # Test single element array
    single_arr = np.array([42], dtype=np.int32)
    arr_bytes, dtype_shape = dumps_numpy_array(single_arr)
    reconstructed = loads_numpy_array(arr_bytes, dtype_shape)
    assert reconstructed.size == 1
    assert reconstructed[0] == 42

    # Test array with zero dimensions
    zero_dim_arr = np.array(42, dtype=np.float64)
    arr_bytes, dtype_shape = dumps_numpy_array(zero_dim_arr)
    reconstructed = loads_numpy_array(arr_bytes, dtype_shape)
    assert reconstructed.size == 1
    assert reconstructed.item() == 42
