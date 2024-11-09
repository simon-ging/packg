import io
import tempfile

from packg.iotools import yield_chunked_bytes


def test_yield_chunked_bytes_tempfile():
    # Create a temporary file with some test data
    test_data = b"1234567890" * 100  # 1,000 bytes of data
    chunk_size = 256

    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        # Write test data to the temporary file
        temp_file.write(test_data)
        temp_file.flush()  # Ensure data is written to disk

        # Read the file in chunks and verify the data
        result = b"".join(yield_chunked_bytes(temp_file.name, chunk_size))
        assert result == test_data, "Data read from temporary file does not match expected data"


def test_yield_chunked_bytes_inmemory():
    # Create an in-memory file-like object with some test data
    test_data = b"abcdefghijklmnopqrstuvwxyz" * 40  # 1,040 bytes of data
    chunk_size = 128
    in_memory_file = io.BytesIO(test_data)

    # Read the in-memory file in chunks and verify the data
    result = b"".join(yield_chunked_bytes(in_memory_file, chunk_size))
    assert result == test_data, "Data read from in-memory file does not match expected data"
