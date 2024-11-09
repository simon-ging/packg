from csv import Error as CsvError

import pytest

from packg.iotools.tsvext import format_to_tsv


def test_format_to_tsv():
    assert format_to_tsv([[1, 2], [3]]) == "1\t2\n3\n"
    assert format_to_tsv([["a", "b"], ["c"]]) == "a\tb\nc\n"
    assert format_to_tsv([["a", "b"], ["c", "d"]]) == "a\tb\nc\td\n"


def test_format_to_tsv_errors():
    with pytest.raises(CsvError):
        format_to_tsv(["a", "b"])  # 1d array instead of 2d

    with pytest.raises(CsvError):
        format_to_tsv([[1, 2], "b"])  # 1d array instead of 2d, for 2nd row

    with pytest.raises(CsvError):
        format_to_tsv("abc")  # str instead of 2d array
