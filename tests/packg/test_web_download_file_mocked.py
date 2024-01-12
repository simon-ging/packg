"""
Test downloader function with a mocked urllib3 response
"""
from packg.web import download_file


class _MockHTTPResponse:
    """Mock for urllib3.HTTPResponse"""

    def __init__(self, data, headers=None, status=200):
        if headers is None:
            headers = {}
        self.data = data
        self.headers = headers
        self.status = status

    def read(self, chunk_size):
        chunk = self.data[:chunk_size]
        self.data = self.data[chunk_size:]
        return chunk

    def close(self):
        pass


def test_download_file(monkeypatch, tmpdir_factory):
    mock_data = b"hello" * 100  # 500 bytes

    # monkeypatch urllib request to return the mock response
    def mock_request(*_args, **_kwargs):
        return _MockHTTPResponse(mock_data, headers={"Content-Length": "500"})

    monkeypatch.setattr("packg.web.urllib3.PoolManager.request", mock_request)

    # # version with: from unittest.mock import Mock, MagicMock
    # response = _MockHTTPResponse(data, headers={"Content-Length": "500"})
    # mock_request = Mock(return_value=response)
    # mock_pool_manager = MagicMock()
    # mock_pool_manager.request = mock_request
    # monkeypatch.setattr("packg.web.urllib3.PoolManager", lambda: mock_pool_manager)

    # Test download to temp file
    tmpdir = tmpdir_factory.mktemp("test_web")
    tmp_file = tmpdir / "downloaded_file.txt"
    num_bytes = download_file(tmp_file, "http://example.com", verbose=False, pbar=False)
    assert num_bytes == 500

    # Test resuming by downloading the next 500 bytes
    mock_data = b"world" * 100  # 500 bytes
    response = _MockHTTPResponse(mock_data, headers={"Content-Length": "500"})
    mock_request.return_value = response

    num_bytes = download_file(tmp_file, "http://example.com", verbose=False, pbar=False)
    assert num_bytes == 500

    # Validate the content of the downloaded file
    with open(tmp_file, "rb") as f:
        content = f.read()
    assert content == b"hello" * 100 + b"world" * 100
