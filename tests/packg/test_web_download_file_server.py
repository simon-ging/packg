"""
Test downloader function by running a local webserver for the test session
"""

from typing import Tuple

import pytest

from packg.testing.fixture_webserver import BIN_CONTENT, BIN_FILE, TXT_CONTENT, TXT_FILE, webserver
from packg.web import download_file


@pytest.mark.parametrize(
    "file, expected_content, is_utf8",
    [
        pytest.param(BIN_FILE, BIN_CONTENT, False, id="binary_file"),
        pytest.param(TXT_FILE, TXT_CONTENT, True, id="utf8_file"),
    ],
)
def test_download_file(file: str, expected_content, is_utf8, webserver: Tuple[str, int], tmp_path):
    host, port = webserver
    print(f"host: {host} port: {port}")

    file_path = tmp_path / file
    file_url = f"http://{host}:{port}/{file}"
    _n_bytes = download_file(file_path, file_url, verbose=True, pbar=False, chunk_size=1024)

    if is_utf8:
        downloaded_content = file_path.read_text(encoding="utf-8")
    else:
        downloaded_content = file_path.read_bytes()
    assert (
        downloaded_content == expected_content
    ), f"Content mismatch: {downloaded_content[:10]}... != {expected_content[:10]}..."
