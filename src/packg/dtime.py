"""
Utilities for calendar dates and times.

Note: If more timezones than system and UTC are required, use pytz package
"""
import datetime
from typing import Optional


def _datetime_now(tz=None):  # this function allows to mock datetime.now() in tests
    return datetime.datetime.now(tz=tz)


def get_system_timezone() -> datetime.tzinfo:
    return datetime.datetime.now().astimezone().tzinfo


def get_utc_timezone() -> datetime.tzinfo:
    # print(type(datetime.timezone(datetime.timedelta(minutes=0))))
    return datetime.timezone(datetime.timedelta(minutes=0))


def get_timestamp_for_filename(dtime: Optional[datetime.datetime] = None, tz=None) -> str:
    """
    Convert datetime to timestamp for filenames.

    Args:
        dtime: Optional datetime object, will use now() if not given.
        tz: Optional timezone object for using now(), will use system timezone if not given.

    Returns:
        string like 1970_12_31_23_59_59
    """
    if dtime is None:
        dtime = _datetime_now(tz=tz)
    ts = dtime.strftime("%Y_%m_%d_%H_%M_%S")
    return ts


def format_seconds_adaptive(seconds: float, format_str="{:.1f}{}"):
    """
    Format seconds to adaptive time format depending on the size of the input.

    Args:
        seconds: number of seconds
        format_str: format string for number and time unit

    Returns:
        string like 1.2s, 1.2min, 1.2h, 1.2d
    """
    abs_seconds = abs(seconds)
    if abs_seconds < 60:
        number = seconds
        unit = "s"
    elif abs_seconds < 3600:
        number = seconds / 60
        unit = "min"
    elif abs_seconds < 3600 * 24:
        number = seconds / 3600
        unit = "h"
    elif abs_seconds < 3600 * 24 * 7:
        number = seconds / (3600 * 24)
        unit = "d"
    elif abs_seconds < 3600 * 24 * 365:
        number = seconds / (3600 * 24 * 7)
        unit = "w"
    else:
        number = seconds / (3600 * 24 * 365)
        unit = "y"
    return format_str.format(number, unit)


def format_timestamp(
    timestamp: Optional[int] = None,
    format_str="%Y-%m-%d %H:%M:%S",
    tz=None,
) -> str:
    """
    Format a unix timestamp as date.

    Args:
        timestamp: unix timestamp
        format_str: output format
        tz: Optional timezone object for using now(), will use system timezone if not given.

    Returns:
        date string
    """
    if timestamp is None:
        dt_object = _datetime_now(tz=tz)
    else:
        dt_object = datetime.datetime.fromtimestamp(timestamp, tz=tz)
    return dt_object.strftime(format_str)
