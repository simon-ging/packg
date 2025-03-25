import pytest
import sys
from unittest.mock import patch
import shutil
import os
from packg.__main__ import main


def test_main_no_args(capsys):
    # Mock sys.argv to simulate no arguments
    with patch.object(sys, "argv", ["packg"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        # Check if usage info is printed
        captured = capsys.readouterr()
        assert "Usage: packg <module> <*args>" in captured.out
        # Check that we get a formatted list of modules
        assert "caching" in captured.out
        assert "cli." in captured.out
        assert "iotools." in captured.out


def test_main_invalid_module():
    # Test with non-existent module
    with patch.object(sys, "argv", ["packg", "nonexistent_module"]):
        with pytest.raises(ValueError) as exc_info:
            main()
        assert "Module packg.nonexistent_module not found" in str(exc_info.value)


@pytest.mark.parametrize("terminal_size", [(80, 24), (100, 30)])
def test_main_terminal_size(terminal_size, capsys):
    # Mock terminal size and test output formatting
    with patch.object(sys, "argv", ["packg"]):
        with patch.object(
            shutil, "get_terminal_size", return_value=os.terminal_size(terminal_size)
        ):
            with pytest.raises(SystemExit):
                main()
            captured = capsys.readouterr()
            assert len(max(captured.out.split("\n"), key=len)) <= terminal_size[0]


def test_main_with_valid_module():
    # Create a mock module with a main function
    mock_module = type("MockModule", (), {"main": lambda: None})

    with patch("importlib.util.find_spec") as mock_find_spec:
        with patch("importlib.import_module", return_value=mock_module):
            mock_find_spec.return_value = type(
                "MockSpec", (), {"origin": "/path/to/mock_module.py"}
            )

            # Test with a valid module name
            with patch.object(sys, "argv", ["packg", "valid_module", "arg1", "arg2"]):
                main()
                # Check if sys.argv was properly modified
                assert sys.argv == ["/path/to/mock_module.py", "arg1", "arg2"]
