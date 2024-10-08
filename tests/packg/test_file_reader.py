from io import StringIO

from packg.iotools.file_reader import read_text_from_file_or_io


def test_read_text_from_file_or_io():
    text = "Hello, World!"
    file_like = StringIO(text)
    result = read_text_from_file_or_io(file_like)
    assert result == text
