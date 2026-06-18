import pytest

from packg.tqdmext import tqdm_max_ncols


@pytest.mark.parametrize(
    "ncols, max_ncols, expected",
    [
        (200, 50, 50),  # terminal wider than max_ncols: clamp to max_ncols
        (200, 300, 200),  # terminal narrower than max_ncols: keep terminal width
        (200, None, 200),  # max_ncols=None disables clamping
    ],
)
def test_max_ncols_clamps_width(ncols, max_ncols, expected):
    """tqdm_max_ncols clamps the bar width to max_ncols. The terminal width is set via tqdm's
    public ``ncols`` kwarg."""
    pbar = tqdm_max_ncols(range(10), ncols=ncols, max_ncols=max_ncols, disable=False)
    assert pbar.ncols == expected
    pbar.close()


def test_max_ncols_undetected_terminal():
    """When tqdm cannot detect the terminal width (output is not a tty) it sets ncols to None.
    tqdm_max_ncols leaves ncols as None and does not crash on the clamp."""
    pbar = tqdm_max_ncols(range(10), max_ncols=50, disable=False)
    assert pbar.ncols is None
    pbar.close()


def test_initialization():
    """Test that tqdm_max_ncols initializes without errors."""
    pbar = tqdm_max_ncols(range(10))
    pbar.close()


def test_disable_true():
    """Test the behavior when self.disable is True."""
    pbar = tqdm_max_ncols(range(10), disable=True)
    assert not hasattr(pbar, "ncols")  # in disabled case, ncols is unset
    pbar.close()
