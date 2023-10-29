import sys

import pytest

from packg.tqdmu import tqdm_max_ncols


@pytest.mark.parametrize(
    "os_detected",
    [
        pytest.param(True, id="true"),
        pytest.param(False, id="false"),
    ],
)
def test_max_ncols(os_detected, monkeypatch):
    """Test that ncols is set to max_ncols."""
    max_columns = 50
    expected_max_columns = max_columns

    # must patch the screen shape because that isnt available when running as test in background
    with monkeypatch.context() as m:
        for fn_name in [
            "_screen_shape_windows",
            "_screen_shape_tput",
            "_screen_shape_linux",
        ]:
            if os_detected:
                m.setattr(f"tqdm.utils.{fn_name}", lambda x: (80, 200))
            else:
                m.setattr(f"tqdm.utils.{fn_name}", None)  # would happen if OS is not detected
        from tqdm.utils import _screen_shape_wrapper  # noqa

        screen_shape_fn = _screen_shape_wrapper()
        if screen_shape_fn is not None:
            screen_shape = screen_shape_fn(sys.stderr)
            assert screen_shape == (80, 200), (
                f"screen shape fn was not properly mocked: "
                f"Got {screen_shape} from {screen_shape_fn}"
            )
        else:
            # OS was not detected by tqdm so ncols will be none
            expected_max_columns = None

        pbar = tqdm_max_ncols(range(10), max_ncols=max_columns, disable=False)
        assert pbar.ncols == expected_max_columns
        pbar.close()

        # max_ncols=none enables default behaviour of tqdm
        pbar = tqdm_max_ncols(range(10), max_ncols=None)
        assert (expected_max_columns is None and pbar.ncols is None) or pbar.ncols == 80
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
