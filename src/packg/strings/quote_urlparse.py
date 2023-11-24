import urllib.parse


def quote_with_urlparse(sentence: str, prefix: str = "") -> str:
    """
    Quote the input s.t. it is safe for using in a URL.
    Useful also for e.g. using the input
    as file names.

    Args:
        sentence: input string
        prefix: prefix to add to the quoted string, useful to avoid empty return strings

    Returns:
        quoted string
    """

    quoted = urllib.parse.quote(sentence, safe="")
    return f"{prefix}{quoted}"


def unquote_with_urlparse(sentence: str, prefix: str = "") -> str:
    sentence_no_prefix = sentence[len(prefix) :]
    return urllib.parse.unquote(sentence_no_prefix)
