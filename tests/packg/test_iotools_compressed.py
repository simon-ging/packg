import io
import os

from packg.iotools.compressed import (
    CompressorConst,
    get_compressor,
    get_decompressor,
    DecompressorInterface,
)


def test_compression():
    raw_data = os.urandom(1024) * 10
    chunk_size = 400

    print(f"raw data length {len(raw_data)}")

    for compressor_name in CompressorConst.values():
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


def main():
    test_compression()


if __name__ == "__main__":
    main()
