import numpy as np
import pytest

from packg.stats import AvgMetric, ensure_numpy


def test_initial_state():
    metric = AvgMetric()
    assert metric.count == 0
    assert metric.avg == 0.0


def test_reset():
    metric = AvgMetric()
    metric.count = 5
    metric.avg = 10.0
    metric.reset()
    assert metric.count == 0
    assert metric.avg == 0.0


def test_single_update():
    metric = AvgMetric()
    metric.update(10.0)
    assert metric.count == 1
    assert metric.avg == 10.0


def test_multiple_updates():
    metric = AvgMetric()
    values = [10.0, 20.0, 30.0]
    for val in values:
        metric.update(val)
    assert metric.count == len(values)
    assert metric.avg == sum(values) / len(values)


def test_update_with_n():
    metric = AvgMetric()
    metric.update(10.0, n=5)
    assert metric.count == 5
    assert metric.avg == 10.0

    metric.update(20.0, n=5)
    assert metric.count == 10
    assert metric.avg == 15.0


def test_update_with_zero_n():
    metric = AvgMetric()
    with pytest.raises(ValueError):
        metric.update(10.0, n=0)


def test_negative_n():
    metric = AvgMetric()
    with pytest.raises(ValueError):
        metric.update(10.0, n=-1)


def test_ensure_numpy():
    array = [1, 2, 3]
    np_array = ensure_numpy(array)
    assert isinstance(np_array, np.ndarray)


def test_avg_metric():
    metric = AvgMetric()
    metric.update(10, 2)
    assert metric.avg == 10
    metric.update(20, 2)
    assert metric.avg == 15
    metric.update(10, 6)
    assert metric.avg == 12
