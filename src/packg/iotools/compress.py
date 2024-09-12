"""
possible improvements:
    - add more hyperparameters to the compressor wrappers, currently using mostly the defaults.
    - auto compressor name from filename
    - compressor ios similar to BytesIO that compress/decompress as needed on write/read

"""

import lzma
import time
import zstandard
from datetime import datetime
from typing import Union

from packg import Const
from packg.iotools import read_bytes_from_file_or_io, open_file_or_io


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


class CompressorC(Const, str):
    NONE = "none"
    LZMA = "lzma"
    ZSTD = "zstd"
    ZSTD_SLOW = "zstd_slow"


class CompressorInterface:
    def compress(self, data: bytes) -> bytes:
        raise NotImplementedError

    def flush(self) -> bytes:
        raise NotImplementedError

    def compress_once(self, data: bytes) -> bytes:
        return b"".join([self.compress(data), self.flush()])


class DecompressorInterface:
    def decompress(self, data: bytes) -> bytes:
        raise NotImplementedError

    def flush(self) -> bytes:
        return b""

    def decompress_once(self, data: bytes) -> bytes:
        return self.decompress(data)


def decompress_file_to_bytes(file_or_io, compressor_name: str, **compressor_kwargs) -> bytes:
    data_bytes_compressed = read_bytes_from_file_or_io(file_or_io)
    return decompress_bytes_to_bytes(data_bytes_compressed, compressor_name, **compressor_kwargs)


def decompress_bytes_to_bytes(
    data_bytes_compressed: bytes, compressor_name: str, **compressor_kwargs
) -> bytes:
    decompressor = get_decompressor(compressor_name, **compressor_kwargs)
    return decompressor.decompress_once(data_bytes_compressed)


def decompress_file_to_str(
    file_or_io, compressor_name: str, encoding: str = "utf-8", **compressor_kwargs
) -> str:
    data_bytes_compressed = read_bytes_from_file_or_io(file_or_io)
    return decompress_bytes_to_str(
        data_bytes_compressed, compressor_name, encoding, **compressor_kwargs
    )


def decompress_bytes_to_str(
    data_bytes_compressed: bytes, compressor_name: str, encoding: str = "utf-8", **compressor_kwargs
) -> str:
    data_bytes = decompress_bytes_to_bytes(
        data_bytes_compressed, compressor_name, **compressor_kwargs
    )
    return data_bytes.decode(encoding)


def compress_data_to_bytes(
    data: Union[str, bytes], compressor_name: str, encoding: str = "utf-8", **compressor_kwargs
) -> bytes:
    if isinstance(data, str):
        data = data.encode(encoding)
    compressor = get_compressor(compressor_name, len(data), **compressor_kwargs)
    return compressor.compress_once(data)


def compress_data_to_file(
    data: Union[str, bytes],
    file_or_io,
    compressor_name: str,
    create_parent: bool = False,
    **compressor_kwargs,
):
    data_bytes = compress_data_to_bytes(data, compressor_name, **compressor_kwargs)
    with open_file_or_io(file_or_io, mode="wb", create_parent=create_parent) as fh:
        fh.write(data_bytes)


# noinspection PyArgumentList
def get_compressor(compressor_name: str, size: int = -1, **kwargs) -> CompressorInterface:
    """
    Args:
        compressor_name: name of the algorithm
        size: total size of the data that will be compressed.
            some compression algorithms can benefit from knowing this. default -1 = unknown
        **kwargs: parameters for the specific compressor

    Returns:
        compressor
    """
    if compressor_name == CompressorC.NONE:
        return DummyCompressor(**kwargs)
    if compressor_name == CompressorC.LZMA:
        return LzmaCompressorWrapper(**kwargs)
    if compressor_name == CompressorC.ZSTD:
        return ZstdCompressorWrapper(size=size, **kwargs)
    if compressor_name == CompressorC.ZSTD_SLOW:
        return ZstdCompressorWrapper(size=size, level=9, **kwargs)
    raise ValueError(f"Unknown compressor {compressor_name}")


# noinspection PyArgumentList
def get_decompressor(compressor_name: str, **kwargs) -> DecompressorInterface:
    """

    Args:
        compressor_name: name of the algorithm
        **kwargs: parameters for the specific decompressor

    Returns:
        decompressor
    """
    if compressor_name == CompressorC.NONE:
        return DummyDecompressor(**kwargs)
    if compressor_name == CompressorC.LZMA:
        return LzmaDecompressorWrapper(**kwargs)
    if compressor_name in (CompressorC.ZSTD, CompressorC.ZSTD_SLOW):
        return ZstdDecompressorWrapper(**kwargs)
    raise ValueError(f"Unknown compressor {compressor_name}")


class DummyCompressor(CompressorInterface):
    def compress(self, data: bytes) -> bytes:
        return data

    def flush(self) -> bytes:
        return b""


class DummyDecompressor(DecompressorInterface):
    def decompress(self, data: bytes) -> bytes:
        return data


class ZstdCompressorWrapper(CompressorInterface):
    def __init__(self, size=-1, level=3, threads=0):
        self.cctx = zstandard.ZstdCompressor(level=level, threads=threads)
        self.compressor = self.cctx.compressobj(size=size)

    def compress(self, data: bytes) -> bytes:
        return self.compressor.compress(data)

    def flush(self) -> bytes:
        return self.compressor.flush(zstandard.FLUSH_FRAME)


class ZstdDecompressorWrapper(DecompressorInterface):
    def __init__(self):
        self.cctx = zstandard.ZstdDecompressor()
        self.decompressor = self.cctx.decompressobj()

    def decompress(self, data: bytes) -> bytes:
        return self.decompressor.decompress(data)


class LzmaCompressorWrapper(CompressorInterface):
    def __init__(self):
        self.lzc = lzma.LZMACompressor()

    def compress(self, data: bytes) -> bytes:
        return self.lzc.compress(data)

    def flush(self) -> bytes:
        return self.lzc.flush()


class LzmaDecompressorWrapper(DecompressorInterface):
    def __init__(self):
        self.lzd = lzma.LZMADecompressor()

    def decompress(self, data: bytes) -> bytes:
        return self.lzd.decompress(data)


def read_unzip_list_output(unzip_output: str):
    """
    Args:
        unzip_output: output from unzip -l command

    Returns:
        dict: filename -> (size, timestamp)
    """
    result = {}
    lines = unzip_output.strip().splitlines()

    for line in lines:
        parts = line.split()
        if len(parts) < 4 or not parts[0].isdigit():
            continue

        size = int(parts[0])
        date_str = parts[1]
        time_str = parts[2]
        filename = " ".join(parts[3:])

        # Combine date and time strings to create a timestamp
        timestamp_str = f"{date_str} {time_str}"
        timestamp = time.mktime(datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M").timetuple())

        result[filename] = (size, timestamp)

    return result
