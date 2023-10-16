import pytest

from packg.stats import AvgMetric


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
