"""
possible improvements:
    - add more hyperparameters to the compressor wrappers, currently using mostly the defaults.

"""
import lzma

import zstandard
from packg import Const


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


class CompressorConst(Const):
    NONE = "none"
    LZMA = "lzma"
    ZSTD = "zstd"
    ZSTD_SLOW = "zstd_slow"


class CompressorInterface:
    def compress(self, data: bytes) -> bytes:
        raise NotImplementedError

    def flush(self) -> bytes:
        raise NotImplementedError


class DecompressorInterface:
    def decompress(self, data: bytes) -> bytes:
        raise NotImplementedError

    def flush(self) -> bytes:
        raise NotImplementedError


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
    if compressor_name == CompressorConst.NONE:
        return DummyCompressor(**kwargs)
    if compressor_name == CompressorConst.LZMA:
        return LzmaCompressorWrapper(**kwargs)
    if compressor_name == CompressorConst.ZSTD:
        return ZstdCompressorWrapper(size=size, **kwargs)
    if compressor_name == CompressorConst.ZSTD_SLOW:
        return ZstdCompressorWrapper(size=size, level=10, **kwargs)
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
    if compressor_name == CompressorConst.NONE:
        return DummyDecompressor(**kwargs)
    if compressor_name == CompressorConst.LZMA:
        return LzmaDecompressorWrapper(**kwargs)
    if compressor_name in (CompressorConst.ZSTD, CompressorConst.ZSTD_SLOW):
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

    def flush(self) -> bytes:
        return b""


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

    def flush(self) -> bytes:
        return self.decompressor.flush()


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

    def flush(self) -> bytes:
        return b""
