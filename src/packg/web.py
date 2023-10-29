import socket
import sys
from pathlib import Path
from pprint import pprint
from typing import Dict, Tuple, Union, BinaryIO

import urllib3
from tqdm import tqdm

# socket
_module = sys.modules[__name__]


def disable_socket(verbose: bool = True):
    """disable socket.socket to disable the Internet. useful in testing.
    from https://gist.github.com/hangtwenty/9200597e3be274c79896
    """
    setattr(_module, "_socket_disabled", True)
    original_socket = socket.socket

    def guarded(*args, **kwargs):
        do_raise = True
        if getattr(_module, "_socket_disabled", False) and do_raise:
            raise RuntimeError(
                "A test tried to use socket.socket without explicitly un-blocking it."
            )
        socket.socket = original_socket
        return socket.socket(*args, **kwargs)

    socket.socket = guarded
    if verbose:
        print("[!] socket.socket is now blocked. The network should be inaccessible.")


def enable_socket(verbose: bool = True):
    """re-enable socket.socket to enable the Internet."""
    setattr(_module, "_socket_disabled", False)
    if verbose:
        print("[!] socket.socket is UN-blocked, and the network can be accessed.")


def _open_file_for_download(file: Union[str, Path]) -> Tuple[Dict[str, str], BinaryIO]:
    """Open given file pointer for download and create a header to download the remainder partially.

    Args:
        file: File path.

    Returns:

    """
    file = Path(file)
    if file.is_file():
        # file exists, download remainder (nothing if download is complete)
        fsize = file.stat().st_size
        fh = file.open("ab")
    else:
        # load entire file
        fsize = 0
        fh = file.open("wb")
    headers = {"Range": f"bytes={fsize}-"}
    return headers, fh


def download_file(
    file: Union[str, Path],
    url: str,
    verbose: bool = False,
    pbar: bool = True,
    chunk_size=1024**2,
    req_header=None,
) -> int:
    """
    Download file from url.
    """
    if req_header is None:
        req_header = {}
    http = urllib3.PoolManager()
    file = Path(file)

    # support partial file downloading
    headers, fh = _open_file_for_download(file)
    headers.update(req_header)
    req: urllib3.HTTPResponse = http.request("GET", url, preload_content=False, headers=headers)
    if verbose:
        pprint(req.headers.items())

    # check how much content is left
    try:
        web_size = int(req.headers["Content-Length"])
    except KeyError:
        web_size = 1024

    # read 1MB at a time from the result
    num_bytes = 0
    if web_size == 0 or req.status == 416:
        # html code 416: range (of 0 B) not satisfiable
        if verbose:
            print(f"already downloaded.")
    else:
        if verbose or pbar:
            print(f"Downloading {web_size / 1024 ** 2:.3f} MB")
        if pbar:
            pb = tqdm(total=web_size, unit_scale=True, unit="B", unit_divisor=1024)
        while True:
            data = req.read(chunk_size)  # type: bytes
            if pbar:
                pb.update(chunk_size)
            if verbose:
                print(f"{len(data)} bytes read")
            if len(data) == 0:
                break
            fh.write(data)
            num_bytes += len(data)
        if pbar:
            pb.close()
    req.close()
    fh.close()

    if verbose:
        print(f"Downloaded {num_bytes / 1024 ** 2:.3f}MB from", url)
    return num_bytes
