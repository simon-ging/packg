from __future__ import annotations

import re


def dict_to_str_comma_equals(in_dict: dict[str, any] | list[tuple[any, any]]):
    try:
        items = in_dict.items()
    except AttributeError:
        items = in_dict
    str_list = []
    for k, v in items:
        str_list.append(f"{k}={v}")
    return ", ".join(str_list)


def clean_string_for_filename(input_str):
    """
    Clean string to make it less annoying when used as a filename.

    Replace spaces and some other special characters with underscores,
    then remove any multiple underscores and underscore at the beginning or end.
    """
    output_str = input_str
    output_str = output_str.replace('"', "_")
    output_str = re.sub(r"\s+", "_", output_str)
    output_str = re.sub(r"[()\[\]{}&*?!<>|\\/:;\"']", "_", output_str)
    output_str = re.sub(r"_+", "_", output_str)
    output_str = re.sub(r"^_+", "", output_str)
    output_str = re.sub(r"_+$", "", output_str)
    return output_str
