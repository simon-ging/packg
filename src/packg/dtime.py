from datetime import datetime
from typing import Optional


def _datetime_now():  # this function allows to mock datetime.now() in tests
    return datetime.now()


def get_timestamp_for_filename(dtime: Optional[datetime] = None) -> str:
    """
    Convert datetime to timestamp for filenames.

    Args:
        dtime: Optional datetime object, will use now() if not given.

    Returns:
        string like 1970_12_31_23_59_59
    """
    if dtime is None:
        dtime = _datetime_now()
    ts = str(dtime).split(".", maxsplit=1)[0].replace(" ", "_").replace(":", "_").replace("-", "_")
    return ts


def format_seconds_adaptive(seconds:float, format_str="{:.1f}{}"):
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
    else:
        number = seconds / (3600 * 24)
        unit = "d"
    return format_str.format(number, unit)
