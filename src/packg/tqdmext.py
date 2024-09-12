"""
Wrapper for tqdm progressbar with default settings.

Note about smoothing:
    Smoothing: 0=compute average speed, 1=compute current speed
    (math: EMAcurrent = (1 − smoothing) * EMAprevious + smoothing * valuecurrent)
    Default is 0.3
"""

from __future__ import annotations
from attrs import define, field
from timeit import default_timer
from tqdm import tqdm
from typing import Optional

from packg.strings.formatters import dict_to_str_comma_equals

TQDM_WID = 100


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


@define
class SimplePbar:
    interval: int | None = None
    total: int | None = None
    print_fn: callable = print
    print_end: str = "\n"
    time_fmt: str = "m"
    t1: float = field(init=False)
    time_fmt_div: int = field(init=False)
    current: int = field(init=False)
    len_total_fmt: int = field(init=False)

    def __attrs_post_init__(self):
        self.reset()

    def reset(self):
        self.t1 = default_timer()
        self.current = 0
        self.len_total_fmt = 1
        if self.total is not None:
            self.len_total_fmt = len(str(self.total))

        if self.interval is None:
            if self.total is not None:
                self.interval = int(max(1, self.total // 10))
            else:
                self.interval = 1
        if self.time_fmt == "s":
            self.time_fmt_div = 1
        elif self.time_fmt == "m":
            self.time_fmt_div = 60
        elif self.time_fmt == "h":
            self.time_fmt_div = 3600
        elif self.time_fmt == "d":
            self.time_fmt_div = 86400
        else:
            raise ValueError(f"Invalid time_fmt {self.time_fmt}")

    def update(self, n: int = 1, status_counts: dict[str, int] | None = None):
        self.current += n
        if (self.current - 1) % self.interval != 0:
            return
        delta_t = default_timer() - self.t1
        delta_n = max(self.current, 1)
        current_fmt = f"{self.current:{self.len_total_fmt}d}"
        outputs = [f"{current_fmt}"]
        if self.total is not None:
            remaining_t = delta_t / delta_n * (self.total - self.current)
            outputs.append(
                f"/{self.total} Remaining {remaining_t / self.time_fmt_div:.2f}{self.time_fmt}"
            )
        outputs.append(f" Elapsed {delta_t / self.time_fmt_div:.2f}{self.time_fmt}")
        if status_counts is not None:
            outputs.append(f" {dict_to_str_comma_equals(dict(status_counts))}")
        output = " ".join(outputs)
        self.print_fn(output, end=self.print_end)
