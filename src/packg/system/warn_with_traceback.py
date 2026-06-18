import os
import sys
import traceback
import warnings

def warn_with_traceback(message, category, filename, lineno, file=None, line=None):
    """show warnings with traceback"""
    traceback.print_stack(file=sys.stderr)
    sys.stderr.write(warnings.formatwarning(message, category, filename, lineno, line))


def _running_under_pytest() -> bool:
    return "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ


if not _running_under_pytest():
    warnings.showwarning = warn_with_traceback

