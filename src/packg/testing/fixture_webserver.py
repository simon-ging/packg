"""
Some reusable fixtures and example setups for writing the tests.
"""

import threading
from functools import partial
from http import server
from pathlib import Path

import pytest

BIN_FILE = "test.bin"
TXT_FILE = "test.test"
BIN_CONTENT = b"test" * 1000
TXT_CONTENT = "ütest" * 1000


@pytest.fixture(scope="session")
def webserver(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("test_io_web")
    (Path(tmp_path) / BIN_FILE).write_bytes(BIN_CONTENT)
    (Path(tmp_path) / TXT_FILE).write_text(TXT_CONTENT, encoding="utf-8")
    print(f"Created path for temporary webserver: {tmp_path}")

    address = ("localhost", 0)  # port=0 means to select an arbitrary unused port
    handler_class = partial(server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    http_server = server.ThreadingHTTPServer(address, handler_class)

    host, port = http_server.socket.getsockname()[:2]
    print(f"Serving HTTP on (http://{host}:{port}/) ...")

    thread = threading.Thread(target=http_server.serve_forever)
    thread.daemon = True
    thread.start()

    yield host, port

    print(f"Closing server...")
    http_server.shutdown()
    thread.join()
