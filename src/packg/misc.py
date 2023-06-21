import traceback


def format_exception(e, with_traceback=False):
    error_str, error_name = str(e), type(e).__name__
    if error_str == "":
        out_str = error_name
    else:
        out_str = f"{error_name}: {error_str}"

    if not with_traceback:
        return out_str

    tb_list = traceback.format_tb(e.__traceback__)
    tb_str = "".join(tb_list)
    return f"{tb_str}{out_str}"
