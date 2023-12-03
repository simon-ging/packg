from packg import format_exception


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
