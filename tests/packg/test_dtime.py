from datetime import datetime

from packg import dtime
from packg.dtime import (
    format_seconds_adaptive,
    format_timestamp,
    get_timestamp_for_filename,
    get_utc_timezone,
)

# in order for the test to work everywhere we must fix the timezone
utc = get_utc_timezone()


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
        m.setattr(dtime, "_datetime_now", lambda tz: datetime_now)
        assert get_timestamp_for_filename() == "2023_10_12_15_30_45"


def test_get_timestamp_for_filename_custom_datetime():
    custom_datetime = datetime(2020, 5, 15, 10, 30, 20)
    assert get_timestamp_for_filename(custom_datetime) == "2020_05_15_10_30_20"


def test_get_timestamp_for_filename_custom_format():
    custom_datetime = datetime(2021, 7, 21, 18, 45, 12)
    timestamp = get_timestamp_for_filename(custom_datetime)
    assert timestamp == "2021_07_21_18_45_12"


def test_format_timestamp_with_given_timestamp():
    timestamp = 1610123456
    expected = "2021-01-08 16:30:56"
    assert format_timestamp(timestamp, tz=utc) == expected


def test_format_timestamp_with_custom_format():
    timestamp = 1610123456
    format_str = "%Y/%m/%d"
    expected = "2021/01/08"
    assert format_timestamp(timestamp, format_str, tz=utc) == expected


def test_format_timestamp_without_timestamp(monkeypatch):
    datetime_now = datetime(2022, 1, 1, 12, 0, 0, tzinfo=utc)
    with monkeypatch.context() as m:
        m.setattr(dtime, "_datetime_now", lambda tz: datetime_now)
        expected = "2022-01-01 12:00:00"
        assert format_timestamp(tz=utc) == expected
