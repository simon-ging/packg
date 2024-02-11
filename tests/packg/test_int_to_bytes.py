import pytest

from packg.maths import convert_unsigned_int_to_bytes, convert_bytes_to_unsigned_int


def test_convert_int_to_bytes_standard():
    assert convert_unsigned_int_to_bytes(12345) == b"\x00\x00\x30\x39"


def test_convert_int_to_bytes_max_int32():
    assert convert_unsigned_int_to_bytes(2**32 - 1, 4) == b"\xff\xff\xff\xff"


def test_convert_int_to_bytes_max_int64():
    assert convert_unsigned_int_to_bytes(2**64 - 1, 8) == b"\xff\xff\xff\xff\xff\xff\xff\xff"


def test_convert_int_to_bytes_zero():
    assert convert_unsigned_int_to_bytes(0) == b"\x00\x00\x00\x00"


def test_convert_int_to_bytes_negative():
    with pytest.raises(OverflowError):
        convert_unsigned_int_to_bytes(-1)


def test_convert_bytes_to_int_standard():
    assert convert_bytes_to_unsigned_int(b"\x00\x00\x30\x39") == 12345


def test_convert_bytes_to_int_max_int32():
    assert convert_bytes_to_unsigned_int(b"\xff\xff\xff\xff") == 2**32 - 1


def test_convert_bytes_to_int_max_int64():
    assert convert_bytes_to_unsigned_int(b"\xff\xff\xff\xff\xff\xff\xff\xff") == 2**64 - 1


def test_convert_bytes_to_int_zero():
    assert convert_bytes_to_unsigned_int(b"\x00\x00\x00\x00") == 0


def test_convert_bytes_to_int_invalid():
    with pytest.raises(ValueError):
        convert_bytes_to_unsigned_int(b"")


def test_round_trip_conversion():
    for val in [0, 12345, 2**32 - 1, 2**64 - 1]:
        assert convert_bytes_to_unsigned_int(convert_unsigned_int_to_bytes(val, length=8)) == val


def test_invalid_input_type():
    with pytest.raises(ValueError):
        convert_unsigned_int_to_bytes("not an int")
