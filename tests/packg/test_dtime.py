from datetime import datetime

from packg import dtime
from packg.dtime import format_seconds_adaptive, get_timestamp_for_filename


def test_format_seconds_adaptive_seconds():
    assert format_seconds_adaptive(30) == "30.0s"
    assert format_seconds_adaptive(-45) == "-45.0s"
    assert format_seconds_adaptive(0) == "0.0s"


def test_format_seconds_adaptive_minutes():
    assert format_seconds_adaptive(120) == "2.0min"
    assert format_seconds_adaptive(-180) == "-3.0min"


def test_format_seconds_adaptive_hours():
    assert format_seconds_adaptive(7200) == "2.0h"
    assert format_seconds_adaptive(-10800) == "-3.0h"


def test_format_seconds_adaptive_days():
    assert format_seconds_adaptive(172800) == "2.0d"
    assert format_seconds_adaptive(-259200) == "-3.0d"


def test_format_seconds_adaptive_custom_format():
    assert format_seconds_adaptive(30, "{:.2f} {}") == "30.00 s"
    assert format_seconds_adaptive(7200, "{:.3f} {}") == "2.000 h"


def test_get_timestamp_for_filename_default(monkeypatch):
    datetime_now = datetime(2023, 10, 12, 15, 30, 45)

    with monkeypatch.context() as m:
        m.setattr(dtime, "_datetime_now", lambda: datetime_now)
        assert get_timestamp_for_filename() == "2023_10_12_15_30_45"


def test_get_timestamp_for_filename_custom_datetime():
    custom_datetime = datetime(2020, 5, 15, 10, 30, 20)
    assert get_timestamp_for_filename(custom_datetime) == "2020_05_15_10_30_20"


def test_get_timestamp_for_filename_custom_format():
    custom_datetime = datetime(2021, 7, 21, 18, 45, 12)
    timestamp = get_timestamp_for_filename(custom_datetime)
    assert timestamp == "2021_07_21_18_45_12"
