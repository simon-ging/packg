import pytest
import tarfile
from pathlib import Path
from io import BytesIO, StringIO
from packg.iotools.compress import (
    CompressorC,
    CompressorInterface,
    DecompressorInterface,
    DummyCompressor,
    DummyDecompressor,
    ZstdCompressorWrapper,
    ZstdDecompressorWrapper,
    LzmaCompressorWrapper,
    LzmaDecompressorWrapper,
    decompress_file_to_bytes,
    decompress_bytes_to_bytes,
    decompress_file_to_str,
    decompress_bytes_to_str,
    compress_data_to_bytes,
    compress_data_to_file,
    get_compressor,
    get_decompressor,
    load_xz,
    dump_xz,
    extract_tar,
    read_unzip_list_output,
)


def test_compressor_interfaces():
    # Test CompressorInterface
    class TestCompressor(CompressorInterface):
        def compress(self, data: bytes) -> bytes:
            return data

        def flush(self) -> bytes:
            return b""

    compressor = TestCompressor()
    assert compressor.compress(b"test") == b"test"
    assert compressor.flush() == b""
    assert compressor.compress_once(b"test") == b"test"

    # Test DecompressorInterface
    class TestDecompressor(DecompressorInterface):
        def decompress(self, data: bytes) -> bytes:
            return data

    decompressor = TestDecompressor()
    assert decompressor.decompress(b"test") == b"test"
    assert decompressor.flush() == b""
    assert decompressor.decompress_once(b"test") == b"test"


def test_dummy_compressors():
    # Test DummyCompressor
    compressor = DummyCompressor()
    assert compressor.compress(b"test") == b"test"
    assert compressor.flush() == b""
    assert compressor.compress_once(b"test") == b"test"

    # Test DummyDecompressor
    decompressor = DummyDecompressor()
    assert decompressor.decompress(b"test") == b"test"
    assert decompressor.flush() == b""
    assert decompressor.decompress_once(b"test") == b"test"


def test_zstd_compressors():
    # Test ZstdCompressorWrapper
    data = b"test data" * 100
    compressor = ZstdCompressorWrapper(size=len(data), level=3, threads=0)
    compressed = compressor.compress_once(data)
    assert len(compressed) < len(data)  # Should be compressed

    # Test ZstdDecompressorWrapper
    decompressor = ZstdDecompressorWrapper()
    decompressed = decompressor.decompress_once(compressed)
    assert decompressed == data


def test_lzma_compressors():
    # Test LzmaCompressorWrapper
    compressor = LzmaCompressorWrapper()
    data = b"test data" * 100
    compressed = compressor.compress_once(data)
    assert len(compressed) < len(data)  # Should be compressed

    # Test LzmaDecompressorWrapper
    decompressor = LzmaDecompressorWrapper()
    decompressed = decompressor.decompress_once(compressed)
    assert decompressed == data


def test_compressor_factory():
    # Test get_compressor
    assert isinstance(get_compressor(CompressorC.NONE), DummyCompressor)
    assert isinstance(get_compressor(CompressorC.LZMA), LzmaCompressorWrapper)
    assert isinstance(get_compressor(CompressorC.ZSTD), ZstdCompressorWrapper)
    assert isinstance(get_compressor(CompressorC.ZSTD_SLOW), ZstdCompressorWrapper)

    with pytest.raises(ValueError, match="Unknown compressor"):
        get_compressor("unknown")

    # Test get_decompressor
    assert isinstance(get_decompressor(CompressorC.NONE), DummyDecompressor)
    assert isinstance(get_decompressor(CompressorC.LZMA), LzmaDecompressorWrapper)
    assert isinstance(get_decompressor(CompressorC.ZSTD), ZstdDecompressorWrapper)
    assert isinstance(get_decompressor(CompressorC.ZSTD_SLOW), ZstdDecompressorWrapper)

    with pytest.raises(ValueError, match="Unknown compressor"):
        get_decompressor("unknown")


def test_compression_functions():
    # Test compress_data_to_bytes
    data = "test data" * 100
    compressed = compress_data_to_bytes(data, CompressorC.ZSTD)
    assert len(compressed) < len(data.encode())

    # Test compress_data_to_file
    file_obj = BytesIO()
    compress_data_to_file(data, file_obj, CompressorC.ZSTD)
    file_obj.seek(0)
    assert len(file_obj.read()) < len(data.encode())


def test_decompression_functions():
    # Test decompress_bytes_to_bytes
    data = b"test data" * 100
    compressed = compress_data_to_bytes(data, CompressorC.ZSTD)
    decompressed = decompress_bytes_to_bytes(compressed, CompressorC.ZSTD)
    assert decompressed == data

    # Test decompress_bytes_to_str
    data_str = "test data" * 100
    compressed = compress_data_to_bytes(data_str, CompressorC.ZSTD)
    decompressed = decompress_bytes_to_str(compressed, CompressorC.ZSTD)
    assert decompressed == data_str

    # Test decompress_file_to_bytes
    file_obj = BytesIO(compressed)
    decompressed = decompress_file_to_bytes(file_obj, CompressorC.ZSTD)
    assert decompressed == data

    # Test decompress_file_to_str
    file_obj = BytesIO(compressed)
    decompressed = decompress_file_to_str(file_obj, CompressorC.ZSTD)
    assert decompressed == data_str


def test_xz_functions():
    # Test load_xz and dump_xz
    data = "test data" * 100
    file_obj = BytesIO()
    dump_xz(data, file_obj)
    file_obj.seek(0)
    loaded = load_xz(file_obj)
    assert loaded == data

    # Test binary mode
    data_bytes = b"test data" * 100
    file_obj = BytesIO()
    dump_xz(data_bytes, file_obj, mode="wb")
    file_obj.seek(0)
    loaded = load_xz(file_obj, mode="rb")
    assert loaded == data_bytes


def test_extract_tar(tmp_path):
    # Create a test tar file
    tar_path = tmp_path / "test.tar"
    with tarfile.open(tar_path, "w") as tar:
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        tar.add(test_file, arcname="test.txt")

    # Test extraction
    extract_dir = tmp_path / "extracted"
    extract_tar(tar_path, extract_dir)
    assert (extract_dir / "test.txt").read_text() == "test content"

    # Test delete_after_extract
    extract_tar(tar_path, extract_dir, delete_after_extract=True)
    assert not tar_path.exists()


def test_read_unzip_list_output():
    unzip_output = """
    Length     Date   Time    Name
    --------- ---------- -----   ----
    1234 2024-03-20 10:00   test1.txt
    5678 2024-03-20 10:01   test2.txt
    """
    result = read_unzip_list_output(unzip_output)
    assert len(result) == 2
    assert result["test1.txt"][0] == 1234
    assert result["test2.txt"][0] == 5678
