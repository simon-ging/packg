import os
import tempfile
from pathlib import Path


from packg.iotools.encoding import (
    detect_encoding,
    detect_encoding_and_read_file,
    detect_encoding_if_needed_and_read_file,
)


def test_detect_encoding():
    # Test with UTF-8 file
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        f.write("Hello, world!".encode("utf-8"))
        f.flush()
        encoding = detect_encoding(f.name)
        assert encoding.lower() == "utf-8" or encoding.lower() == "ascii"
        os.unlink(f.name)

    # Test with UTF-16 file
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        f.write("Hello, world!".encode("utf-16"))
        f.flush()
        encoding = detect_encoding(f.name)
        assert encoding.lower() == "utf-16"
        os.unlink(f.name)


def test_detect_encoding_and_read_file_utf8(tmp_path):
    file = tmp_path / "test.txt"
    content = "Hello, world!"

    file.write_text(content, encoding="utf-8")

    read_content, encoding = detect_encoding_and_read_file(file)

    assert read_content == content
    assert encoding.lower() in {"utf-8", "ascii"}


def test_detect_encoding_if_needed_and_read_file():
    # Test with UTF-8 file
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        content = "Hello, world!"
        f.write(content.encode("utf-8"))
        f.flush()
        read_content, encoding = detect_encoding_if_needed_and_read_file(Path(f.name))
        assert read_content == content
        assert encoding.lower() == "utf-8"
        os.unlink(f.name)

    # Test with UTF-16 file (non-UTF-8)
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        content = "Hello, world!"
        f.write(content.encode("utf-16"))
        f.flush()
        read_content, encoding = detect_encoding_if_needed_and_read_file(Path(f.name))
        assert read_content == content
        assert encoding.lower() == "utf-16"
        os.unlink(f.name)
