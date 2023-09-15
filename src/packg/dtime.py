import datetime
from typing import Optional


def get_timestamp_for_filename(dtime: Optional[datetime.datetime] = None) -> str:
    """
    Convert datetime to timestamp for filenames.

    Args:
        dtime: Optional datetime object, will use now() if not given.

    Returns:
        string like 1970_12_31_23_59_59
    """
    if dtime is None:
        dtime = datetime.datetime.now()
    ts = str(dtime).split(".", maxsplit=1)[0].replace(" ", "_").replace(":", "_").replace("-", "_")
    return ts
