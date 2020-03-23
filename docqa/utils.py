import re
from urllib.parse import urlparse

re_web = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def is_url(text: str) -> bool:
    """
    Check whether piece of string is an url

    >>> is_url('http://foobar.com')
    True
    >>> is_url('http://foobar')
    False
    """
    if not isinstance(text, str):
        return False
    return bool(re_web.match(text))


