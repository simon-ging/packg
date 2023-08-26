import os

from packg.strings.base64utils import b64_encode_from_bytes


def get_random_b64_string(length: int = 40):
    random_bytes_as_b64 = b64_encode_from_bytes(os.urandom(length), url_safe=True)
    # at this point the string is approx 4/3 * length long, cut it down to length
    return random_bytes_as_b64[:length]
