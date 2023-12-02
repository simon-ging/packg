"""Base64 utilities"""


import base64


def _b64_ensure_unsafe(b64str: str):
    """Take a base64 string that is either path-/url-safe or not, and make sure
    it is unsafe, such that the decoder understands it.

    Args:
        b64str: base64 string

    Returns:
        unsafe base64 string
    """
    return b64str.replace("-", "+").replace("_", "/")


def b64_encode_from_bytes(
    bytes_in: bytes, url_safe: bool = True, strip_equals: bool = False
) -> str:
    """Encode bytes with base64.

    Args:
        bytes_in: input bytes to encode
        url_safe: replace "+" with "-" and "/" with "_" to become path/url
            safe, default True
        strip_equals: strip trailing "=" characters. those are only needed to reconstruct the
            length of the original input string.

    Returns:
        path-safe base64 string
    """
    if url_safe:
        out_str = str(base64.urlsafe_b64encode(bytes_in), "ascii")
    else:
        out_str = str(base64.b64encode(bytes_in), "ascii")
    if strip_equals:
        out_str = out_str.rstrip("=")
    return out_str


def b64_decode_to_bytes(b64str: str) -> bytes:
    """Decode a base64 string to bytes

    Args:
        b64str: base64 string

    Returns:
        decoded bytes
    """
    return base64.b64decode(_b64_ensure_unsafe(b64str))


def b64_encode_from_str(str_plain: str, encoding: str = "utf-8", url_safe: bool = True) -> str:
    """Convert string to base64 ascii string

    Args:
        str_plain: input string
        encoding: string encoding, default utf-8
        url_safe: The alphabet uses '-' instead of '+' and '_' instead of '/'.

    Returns:
        base 64 string
    """
    if url_safe:
        return str(base64.urlsafe_b64encode(bytes(str_plain, encoding)), "ascii")
    return str(base64.b64encode(bytes(str_plain, encoding)), "ascii")


def b64_decode_to_str(str_b64: str, encoding: str = "utf-8") -> str:
    """Decode base64 ascii string to original string

    Args:
        str_b64: base64 encoded string
        encoding: result string encoding, default urf-8

    Returns:
        decoded string
    """
    return str(base64.b64decode(bytes(_b64_ensure_unsafe(str_b64), "ascii")), encoding)


def get_random_b64_string(length: int = 40):
    random_bytes_as_b64 = b64_encode_from_bytes(os.urandom(length), url_safe=True)
    # at this point the string is approx 4/3 * length long, cut it down to length
    return random_bytes_as_b64[:length]
