from __future__ import annotations

from pathlib import Path

import chardet


def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
        return result["encoding"]


def detect_encoding_and_read_file(file: Path) -> tuple[str, str]:
    encoding = detect_encoding(file)
    try:
        content = file.read_text(encoding=encoding)
    except UnicodeDecodeError as e:
        raise ValueError(f"Finally failed reading {file} with encoding {encoding}") from e
    return content, encoding


def detect_encoding_if_needed_and_read_file(file: Path) -> str:
    try:
        content = file.read_text(encoding="utf-8")
        encoding = "utf-8"
        return content, encoding
    except UnicodeDecodeError:
        return detect_encoding_and_read_file(file)
