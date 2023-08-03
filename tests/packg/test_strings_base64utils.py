"""Tests for gutil.strings module"""

import pytest

from packg.strings import (
    b64_encode_from_str,
    b64_encode_from_bytes,
    b64_decode_to_str,
    b64_decode_to_bytes,
)


@pytest.fixture
def str_plain():
    return "subjects?_d=1>>>>"


@pytest.fixture
def str_b64():
    return "c3ViamVjdHM/X2Q9MT4+Pj4="


@pytest.fixture
def str_b64_url_safe():
    return "c3ViamVjdHM_X2Q9MT4-Pj4="


@pytest.fixture
def bytes_plain():
    # return b'\x00\x1b\x1d\xff\x0c\xf4'
    return bytes([0, 47, 11, 240, 241, 247, 248, 249, 250, 251, 252, 253, 254, 255])


@pytest.fixture
def bytes_b64():
    return "AC8L8PH3+Pn6+/z9/v8="


@pytest.fixture
def bytes_b64_url_safe():
    return "AC8L8PH3-Pn6-_z9_v8="


def test_b64_encode_str(str_plain, str_b64):
    str_b64_output = b64_encode_from_str(str_plain, url_safe=False)
    assert str_b64 == str_b64_output


def test_b64_encode_str_url_safe(str_plain, str_b64_url_safe):
    str_b64_output = b64_encode_from_str(str_plain)
    assert str_b64_url_safe == str_b64_output


def test_b64_decode_str(str_plain, str_b64):
    str_plain_output = b64_decode_to_str(str_b64)
    assert str_plain == str_plain_output


def test_b64_decode_str_url_safe(str_plain, str_b64_url_safe):
    str_plain_output = b64_decode_to_str(str_b64_url_safe)
    assert str_plain == str_plain_output


def test_b64_encode_bytes(bytes_plain, bytes_b64):
    str_b64_output = b64_encode_from_bytes(bytes_plain, url_safe=False)
    assert bytes_b64 == str_b64_output


def test_b64_encode_bytes_url_safe(bytes_plain, bytes_b64_url_safe):
    str_b64_output = b64_encode_from_bytes(bytes_plain)
    assert bytes_b64_url_safe == str_b64_output


def test_b64_decode_bytes(bytes_plain, bytes_b64):
    bytes_plain_output = b64_decode_to_bytes(bytes_b64)
    assert bytes_plain == bytes_plain_output


def test_b64_decode_bytes_url_safe(bytes_plain, bytes_b64_url_safe):
    bytes_plain_output = b64_decode_to_bytes(bytes_b64_url_safe)
    assert bytes_plain == bytes_plain_output
