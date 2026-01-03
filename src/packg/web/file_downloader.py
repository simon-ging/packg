from pathlib import Path
from pprint import pprint
from typing import BinaryIO, Dict, Optional, Tuple, Union

import urllib3
from tqdm import tqdm

import time
from pathlib import Path

from loguru import logger
from urllib3.exceptions import ProtocolError, SSLError



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


def download_file_with_retries(file, url, sleep_time=1., min_size_mb=0, n_retries=3, raise_on_fail=False) -> Optional[int]:
    n_tries = 0
    while True:
        success = True
        n_tries += 1
        try:
            download_file(file, url, verbose=False, pbar=False)
        except KeyboardInterrupt as e:
            # delete file to avoid having half files leftover
            _delete_ignore_errors(file)
            raise e
        except (ProtocolError, SSLError) as e:
            logger.error(f"Error downloading {url} {file}: {e}")
            success = False
        num_bytes = Path(file).stat().st_size
        if min_size_mb > 0 and num_bytes < min_size_mb * 1024**2:
            logger.warning(
                f"File {file} is too small, retrying after sleep. "
                f"Got: {Path(file).read_text(encoding='utf-8')}"
            )
            success = False
        if success:
            break
        _delete_ignore_errors(file)
        if n_tries >= n_retries:
            logger.error(f"Too many retries for {url} {file}")
            break
        time.sleep(sleep_time)
    if not success:
        if raise_on_fail:
            raise RuntimeError(f"Failed downloading {url} to {file} after {n_retries} tries")
        return None
    return num_bytes

def _delete_ignore_errors(file):
    file = Path(file)
    try:
        file.unlink()
    except Exception as e2:
        logger.error(f"Error deleting file {file}: {e2}")
