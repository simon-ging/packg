from __future__ import annotations


def dict_to_str_comma_equals(in_dict: dict[str, any] | list[tuple[any, any]]):
    try:
        items = in_dict.items()
    except AttributeError:
        items = in_dict
    str_list = []
    for k, v in items:
        str_list.append(f"{k}={v}")
    return ", ".join(str_list)
