"""
Wrapper for tqdm progressbar with default settings.

Note about smoothing:
    Smoothing: 0=compute average speed, 1=compute current speed
    (math: EMAcurrent = (1 − smoothing) * EMAprevious + smoothing * valuecurrent)
    Default is 0.3
"""
from typing import Optional

from tqdm import tqdm

TQDM_WID = 90


class tqdm_max_ncols(tqdm):
    """
    Wrapper for tqdm progressbar with a maximum width. Default max_ncols=90.

    This allows resizing a window later on without breaking the progressbar output.
    Usually tqdm would resize dynamically, but this doesn't always work (e.g. when using screen).
    """

    def __init__(self, *args, max_ncols: Optional[int] = TQDM_WID, **kwargs):
        super().__init__(*args, **kwargs)
        if self.disable:
            # pbar is disabled, no need to modify ncols
            return
        if max_ncols is not None and self.ncols is not None:
            self.ncols = min(self.ncols, max_ncols)
