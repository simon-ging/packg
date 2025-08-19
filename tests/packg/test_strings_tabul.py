from unittest.mock import patch

import pytest

from packg.strings.tabul import format_pseudo_table


def test_format_pseudo_table_basic():
    items = [
        "file1.txt",
        "file2.jpg",
        "file3.pdf",
        "file4.doc",
        "file5.mp3",
        "file6.png",
        "file7.zip",
        "file8.tar.gz",
        "file9.mov",
        "file10.avi",
    ]

    # Test with default terminal width
    with patch("shutil.get_terminal_size") as mock_terminal:
        mock_terminal.return_value.columns = 80
        output = format_pseudo_table(items)
        assert "file1.txt" in output
        assert "file2.jpg" in output
        assert "file3.pdf" in output
        assert "file4.doc" in output
        assert "file5.mp3" in output
        assert "file6.png" in output
        assert "file7.zip" in output
        assert "file8.tar.gz" in output
        assert "file9.mov" in output
        assert "file10.avi" in output


def test_format_pseudo_table_custom_width():
    items = ["a", "b", "c", "d", "e", "f"]
    output = format_pseudo_table(items, max_width=1)  # Only enough for one column
    lines = output.split("\n")
    assert len(lines) == 6  # One item per line
    assert lines[0] == "a"
    assert lines[1] == "b"
    assert lines[2] == "c"
    assert lines[3] == "d"
    assert lines[4] == "e"
    assert lines[5] == "f"


def test_format_pseudo_table_empty():
    output = format_pseudo_table([])
    assert output == ""


def test_format_pseudo_table_single_item():
    output = format_pseudo_table(["single.txt"])
    assert output.strip() == "single.txt"


def test_format_pseudo_table_custom_padding():
    items = ["a", "b", "c"]
    output = format_pseudo_table(items, max_width=20, padding=4)  # Force single row
    assert output == "a    b    c"  # 4 spaces between items


def test_format_pseudo_table_custom_indent():
    items = ["a", "b", "c"]
    output = format_pseudo_table(items, indent=4)
    assert output.startswith("    ")


def test_format_pseudo_table_invalid_input():
    with pytest.raises(ValueError, match="Expected list of strings, got string"):
        format_pseudo_table("not a list")


def test_format_pseudo_table_known_output():
    items = [
        "file1.txt",
        "file2.jpg",
        "file3.pdf",
        "file4.do4234cx",
        "file5.mp3",
        "file6.png",
        "file7.zip",
        "file8.tsdfsar.gz",
        "file9.mov",
        "file10.avi",
        "file11.mkv",
        "file12.234txt",
        "file13.jpg",
        "file14.pdf",
        "file15.docx",
        "file16.mp3",
        "file17.png",
        "filsfde18.zip",
        "fi234234le19.tar.gz",
        "filesdfasdasdf20.mov",
    ]

    with patch("shutil.get_terminal_size") as mock_terminal:
        mock_terminal.return_value.columns = 80
        output = format_pseudo_table(items)
        expected = """\
file1.txt             file8.tsdfsar.gz      file15.docx
file2.jpg             file9.mov             file16.mp3
file3.pdf             file10.avi            file17.png
file4.do4234cx        file11.mkv            filsfde18.zip
file5.mp3             file12.234txt         fi234234le19.tar.gz
file6.png             file13.jpg            filesdfasdasdf20.mov
file7.zip             file14.pdf       """
        assert output.strip() == expected.strip()
