from packg.iotools.misc import format_bytes_human_readable


def test_format_bytes_small():
    assert format_bytes_human_readable(0) == "0.000B"
    assert format_bytes_human_readable(100) == "100.000B"
    assert format_bytes_human_readable(512) == "512.000B"
    assert format_bytes_human_readable(-512) == "-512.000B"


def test_format_bytes_kilobytes():
    assert format_bytes_human_readable(1024) == "1.000KB"
    assert format_bytes_human_readable(2048) == "2.000KB"
    assert format_bytes_human_readable(1536) == "1.500KB"


def test_format_bytes_megabytes():
    assert format_bytes_human_readable(1048576) == "1.000MB"
    assert format_bytes_human_readable(1572864) == "1.500MB"


def test_format_bytes_gigabytes():
    assert format_bytes_human_readable(1073741824) == "1.000GB"
    assert format_bytes_human_readable(1610612736) == "1.500GB"


def test_format_bytes_terabytes():
    assert format_bytes_human_readable(1099511627776) == "1.000TB"
    assert format_bytes_human_readable(1649267441664) == "1.500TB"
