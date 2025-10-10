from __future__ import annotations

import csv
import io
from csv import Error as CsvError


def format_to_tsv(data: list[list[Any]]) -> str:
    """
    Args:
        data: 2d list of list that should be formatted to tsv

    Returns:
        tsv formatted string
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    for i, row in enumerate(data):
        if isinstance(row, str):
            raise CsvError(f"Expected list, got str for row {i} content {row}")
        writer.writerow(row)
    formatted_tsv = output.getvalue()
    output.close()
    return formatted_tsv
