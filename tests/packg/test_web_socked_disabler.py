from pathlib import Path
from typing import Tuple

import pytest

from packg.testing.fixture_webserver import BIN_FILE, webserver
from packg.web import download_file, disable_socket, enable_socket


def test_socket_disabler(webserver: Tuple[str, int], tmp_path: Path):
    host, port = webserver
    file_path = tmp_path / BIN_FILE
    file_url = f"http://{host}:{port}/{BIN_FILE}"

    disable_socket()
    with pytest.raises(RuntimeError):
        download_file(file_path, file_url, verbose=True, pbar=False, chunk_size=1024)

    enable_socket()
    download_file(file_path, file_url, verbose=True, pbar=False, chunk_size=1024)
