import numpy as np
import pytest

from packg.stats import AvgMetric, describe_stats, ensure_numpy


def test_ensure_numpy():
    # Test with numpy array
    arr = np.array([1, 2, 3])
    assert np.array_equal(ensure_numpy(arr), arr)

    # Test with list
    lst = [1, 2, 3]
    assert np.array_equal(ensure_numpy(lst), np.array(lst))

    # Test with numpy-like object (e.g., torch tensor mock)
    class MockTensor:
        def numpy(self):
            return np.array([1, 2, 3])

    mock_tensor = MockTensor()
    assert np.array_equal(ensure_numpy(mock_tensor), np.array([1, 2, 3]))


def test_avg_metric():
    metric = AvgMetric()

    # Test initial state
    assert metric.count == 0
    assert metric.avg == 0.0

    # Test single update
    metric.update(10.0)
    assert metric.count == 1
    assert metric.avg == 10.0

    # Test multiple updates
    metric.update(20.0)
    assert metric.count == 2
    assert metric.avg == 15.0  # (10 + 20) / 2

    # Test update with n > 1
    metric.update(5.0, n=2)
    assert metric.count == 4
    assert metric.avg == 10.0  # (10 + 20 + 5 + 5) / 4

    # Test reset
    metric.reset()
    assert metric.count == 0
    assert metric.avg == 0.0

    # Test invalid n
    with pytest.raises(ValueError, match="n must be > 0 but is 0"):
        metric.update(1.0, n=0)
    with pytest.raises(ValueError, match="n must be > 0 but is -1"):
        metric.update(1.0, n=-1)


def test_describe_stats():
    # Test with basic numpy array
    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    # Test default format (human readable)
    result = describe_stats(arr, name="test")
    assert "test: #5" in result
    assert "Range: 1.00 to 5.00" in result
    assert "mean: 3.00" in result
    assert "std: " in result
    assert "median: 3.00" in result

    # Test with custom format string
    result = describe_stats(arr, name="test", format_str="{:.1f}")
    assert ".0," in result  # Should use one decimal place

    # Test with table separator (e.g., CSV format)
    result = describe_stats(arr, name="test", table_sep=",")
    parts = result.split(",")
    assert len(parts) > 5  # Should have multiple comma-separated values
    assert parts[0] == "test"
    assert parts[1] == "5"  # length of array

    # Test with different types of input
    # List
    result = describe_stats([1.0, 2.0, 3.0], name="list")
    assert "list: #3" in result

    # Mock tensor
    class MockTensor:
        def numpy(self):
            return np.array([1.0, 2.0, 3.0])

    result = describe_stats(MockTensor(), name="tensor")
    assert "tensor: #3" in result
