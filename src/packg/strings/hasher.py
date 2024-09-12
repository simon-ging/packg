import hashlib
import random
from typing import Any

from packg.iotools import dumps_json
from packg.strings.base64tools import b64_encode_from_bytes


def update_hasher_with_json_bytes(hasher, obj: Any) -> bytes:
    hasher.update(dumps_json(obj).encode("utf-8"))


def hash_object(
    obj: Any, hasher_update_fn=update_hasher_with_json_bytes, hasher_cls=hashlib.sha3_224
) -> str:
    """

    Args:
        obj: any object to create a hash for
        hasher_update_fn: function to update the hash object with the python object
        hasher_cls: class to create the hash object

    Returns:
        hash string. url-safe b64 i.e. a-zA-Z0-9 and _-

    """
    hasher = hasher_cls()
    hasher_update_fn(hasher, obj)
    out_hash_bytes = hasher.digest()
    out_hash = b64_encode_from_bytes(out_hash_bytes, strip_equals=True)
    return out_hash


EASY_TO_READ_SYMBOLS = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def get_random_str_id(length: int = 16, symbols: str = EASY_TO_READ_SYMBOLS):
    """
    Get a random string id of given length using the given symbols.

    Args:
        length: length of the id
        symbols: symbols to use for the id

    Returns:
        random string id
    """
    return "".join(random.choices(symbols, k=length))
