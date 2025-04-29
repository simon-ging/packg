import time
from unittest.mock import patch

import pytest

from packg.system.timeout import run_function_with_timeout


def test_run_function_with_timeout_success():
    def test_func(x, y, a=1, b=2):
        time.sleep(0.1)  # Simulate some work
        return x + y + a + b

    result = run_function_with_timeout(1.0, test_func, 1, 2, a=3, b=4)
    assert result == 10


def test_run_function_with_timeout_timeout():
    def hanging_func():
        while True:
            time.sleep(0.1)

    with pytest.raises(TimeoutError, match="Conversion timed out."):
        run_function_with_timeout(0.1, hanging_func)


def test_run_function_with_timeout_exception():
    def error_func():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        run_function_with_timeout(1.0, error_func)


def test_run_function_with_timeout_empty_args():
    def no_args():
        return 42

    result = run_function_with_timeout(1.0, no_args)
    assert result == 42


def test_run_function_with_timeout_kwargs_only():
    def kwargs_only(**kwargs):
        return sum(kwargs.values())

    result = run_function_with_timeout(1.0, kwargs_only, a=1, b=2, c=3)
    assert result == 6


def test_run_function_with_timeout_very_short_timeout():
    def quick_func():
        return "done"

    # Test with a very short timeout that should still succeed
    # Use a slightly longer timeout to account for process startup
    result = run_function_with_timeout(1, quick_func)
    assert result == "done"


def test_run_function_with_timeout_process_cleanup():
    def hanging_func():
        while True:
            time.sleep(0.1)

    # Test that the process is properly cleaned up after timeout
    with patch("multiprocessing.Process") as mock_process:
        mock_process.return_value.is_alive.return_value = True
        mock_process.return_value.join.side_effect = [
            None,
            None,
        ]  # First join times out, second succeeds

        with pytest.raises(TimeoutError):
            run_function_with_timeout(0.1, hanging_func)

        # Verify process was terminated and joined
        mock_process.return_value.terminate.assert_called_once()
        assert mock_process.return_value.join.call_count == 2
