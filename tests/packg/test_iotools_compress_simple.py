import io
import os

from packg.iotools.compress import (
    CompressorC,
    DecompressorInterface,
    compress_data_to_bytes,
    compress_data_to_file,
    decompress_bytes_to_bytes,
    decompress_bytes_to_str,
    decompress_file_to_bytes,
    decompress_file_to_str,
    get_compressor,
    get_decompressor,
)


def test_compression():
    raw_data = os.urandom(1024) * 10
    chunk_size = 400

    print(f"raw data length {len(raw_data)}")

    for compressor_name in CompressorC.values():
        print(f"---------- Testing compressor {compressor_name}")
        compressor = get_compressor(compressor_name)

        sink = io.BytesIO()
        for chunk_start in range(0, len(raw_data), chunk_size):
            chunk = raw_data[chunk_start : chunk_start + chunk_size]
            compressed_chunk = compressor.compress(chunk)
            sink.write(compressed_chunk)
        compressed_chunk = compressor.flush()
        sink.write(compressed_chunk)
        compressed_data = sink.getvalue()
        sink.close()
        print(f"compressed data length {len(compressed_data)}")

        decompressor: DecompressorInterface = get_decompressor(compressor_name)

        sink = io.BytesIO()
        for chunk_start in range(0, len(compressed_data), chunk_size):
            chunk = compressed_data[chunk_start : chunk_start + chunk_size]
            decompressed_chunk = decompressor.decompress(chunk)
            sink.write(decompressed_chunk)
        decompressed_chunk = decompressor.flush()
        sink.write(decompressed_chunk)
        decompressed_data = sink.getvalue()
        sink.close()
        print(f"decompressed data length {len(decompressed_data)}")

        assert raw_data == decompressed_data


def test_convenience_functions(tmp_path_factory):
    raw_data = os.urandom(1024) * 10
    text_data = "Hello World!"
    enc = "utf-8"

    print(f"raw data length {len(raw_data)}")

    for compressor_name in CompressorC.values():
        compressed_bytes = compress_data_to_bytes(raw_data, compressor_name)
        decompressed_bytes = decompress_bytes_to_bytes(compressed_bytes, compressor_name)
        assert raw_data == decompressed_bytes

        sink = io.BytesIO()
        compress_data_to_file(raw_data, sink, compressor_name)
        sink.seek(0)
        decompressed_bytes = decompress_file_to_bytes(sink, compressor_name)
        assert raw_data == decompressed_bytes

        path = tmp_path_factory.mktemp(f"test_compr_{compressor_name}")
        tmpfile = path / "test.bin"
        compress_data_to_file(raw_data, tmpfile, compressor_name)
        decompressed_bytes = decompress_file_to_bytes(tmpfile, compressor_name)
        assert raw_data == decompressed_bytes

        text_compr = compress_data_to_bytes(text_data, compressor_name, encoding=enc)
        text_decomp = decompress_bytes_to_str(text_compr, compressor_name, encoding=enc)
        assert text_data == text_decomp

        sink = io.BytesIO()
        compress_data_to_file(text_data, sink, compressor_name, encoding=enc)
        sink.seek(0)
        text_decomp = decompress_file_to_str(sink, compressor_name, encoding=enc)
        assert text_data == text_decomp

        tmpfile2 = path / "testtxt.bin"
        compress_data_to_file(text_data, tmpfile2, compressor_name, encoding=enc)
        text_decomp = decompress_file_to_str(tmpfile2, compressor_name, encoding=enc)
        assert text_data == text_decomp


def main():
    test_compression()


if __name__ == "__main__":
    main()
