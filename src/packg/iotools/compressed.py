import lzma


def load_xz(file, mode: str = "rt", encoding: str = "utf-8"):
    if "b" in mode:
        encoding = None
    with lzma.open(file, mode, encoding=encoding) as fh:
        data_str = fh.read()
    return data_str


def dump_xz(data, file, mode: str = "wt", encoding: str = "utf-8"):
    if "b" in mode:
        encoding = None
    with lzma.open(file, mode, encoding=encoding) as fh:
        fh.write(data)
