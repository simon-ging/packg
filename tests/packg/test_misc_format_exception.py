from packg import format_exception, format_exception_with_chain


def test_format_exception():
    try:
        var = "test"
        raise ValueError(f"{var}")
    except ValueError as e:
        e_out = format_exception(e, with_traceback=True)
        print()
        print(e_out)
        assert e_out.startswith('  File "'), e_out
        assert e_out.endswith(
            'in test_format_exception\n    raise ValueError(f"{var}")\nValueError: test'
        ), e_out

        e_out = format_exception(e, with_traceback=False)
        print()
        print(e_out)
        assert e_out == "ValueError: test", e_out

        # Test with_source parameter
        e_out = format_exception(e, with_source=True)
        print()
        print(e_out)
        assert "ValueError: test @" in e_out, e_out
        assert "test_misc_format_exception.py:" in e_out, e_out

        # Test with_source and with_traceback together
        e_out = format_exception(e, with_traceback=True, with_source=True)
        print()
        print(e_out)
        assert e_out.startswith('  File "'), e_out
        assert "ValueError: test @" in e_out, e_out


def test_format_exception_empty_message():
    """Test exception with no message"""
    try:
        raise ValueError()
    except ValueError as e:
        e_out = format_exception(e)
        assert e_out == "ValueError", e_out


def test_format_exception_with_chain():
    """Test exception chain formatting"""
    try:
        try:
            raise ValueError("root cause")
        except ValueError as e1:
            raise RuntimeError("middle error") from e1
    except RuntimeError as e2:
        # Test basic formatting
        e_out = format_exception_with_chain(e2)
        print()
        print(e_out)
        assert "cause[0]: ValueError: root cause" in e_out, e_out
        assert "cause[1]: RuntimeError: middle error" in e_out, e_out

        # Test with traceback
        e_out = format_exception_with_chain(e2, with_traceback=True)
        print()
        print(e_out)
        assert "cause[0]:" in e_out, e_out
        assert "cause[1]:" in e_out, e_out
        assert 'File "' in e_out, e_out

        # Test with source
        e_out = format_exception_with_chain(e2, with_source=True)
        print()
        print(e_out)
        assert "cause[0]: ValueError: root cause @" in e_out, e_out
        assert "cause[1]: RuntimeError: middle error @" in e_out, e_out
        assert "test_misc_format_exception.py:" in e_out, e_out


def test_format_exception_with_chain_single():
    """Test format_exception_with_chain with single exception (no chain)"""
    try:
        raise ValueError("single error")
    except ValueError as e:
        e_out = format_exception_with_chain(e)
        assert e_out == "cause[0]: ValueError: single error", e_out


def test_format_exception_no_traceback():
    """Test exception without traceback"""
    e = ValueError("test error")

    # Test with_source when no traceback
    e_out = format_exception(e, with_source=True)
    assert e_out == "ValueError: test error @ <no traceback>", e_out

    # Test with_traceback when no traceback
    e_out = format_exception(e, with_traceback=True)
    assert e_out == "ValueError: test error (no traceback found to format)", e_out
