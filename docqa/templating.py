from typing import Union

from flask import request, url_for
from more_itertools import unique_everseen
from w3lib.url import add_or_replace_parameter, parse_qs, unquote, url_query_parameter, quote, parse_url


def url_sub(url='', **kwargs):
    if not url:
        url = request.url
    for key, value in kwargs.items():
        url = add_or_replace_parameter(url, key, value)
    return url


def url_get_listq(key, sep='.', url=''):
    if not url:
        url = request.url
    return [v for v in url_query_parameter(url, key, default='').split(sep) if v]


def url_get_index(url=''):
    if not url:
        url = request.url
    parsed = parse_url(url)
    path, cur_index = parsed.path.rsplit('/', 1)
    return cur_index


def url_index(index, url=''):
    """
    replace url index with specified index

    >>> url_index(27, 'http://blog.com/show/12')
    'http://blog.com/show/27'
    >>> url_index(-55, 'http://blog.com/show/12?kwarg=foo')
    'http://blog.com/show/-55?kwarg=foo'
    """
    if not url:
        url = request.url
    parsed = parse_url(url)
    path, cur_index = parsed.path.rsplit('/', 1)
    new_path = f"{path}/{index}"
    return parsed._replace(path=new_path).geturl()


def url_add(index, url=''):
    """
    add index

    >>> url_index(27, 'http://blog.com/show/12')
    'http://blog.com/show/12/27'
    >>> url_index('delete', 'http://blog.com/show/12?kwarg=foo')
    'http://blog.com/show/12/delete'
    """
    if not url:
        url = request.url
    parsed = parse_url(url)
    new_path = f"{parsed.path}/{index}"
    return parsed._replace(path=new_path).geturl()


def url_inc(inc=1, url=''):
    """
    increase index in url path by specified value

    >>> url_inc(1, 'http://blog.com/show/12?key=value')
    'http://blog.com/show/13?key=value'
    >>> url_inc(-5, 'http://blog.com/show/12?key=value')
    'http://blog.com/show/7?key=value'
    """
    if not url:
        url = request.url
    parsed = parse_url(url)
    path, index = parsed.path.rsplit('/', 1)
    new_path = f"{path}/{int(index) + inc}"
    return parsed._replace(path=new_path).geturl()


def url_rm_listq(key, value, url='', sep='.'):
    """
    Remove list member from a url query parameter

    >>> url_rm_listq('hide', 'two', url='http://blog.com?hide=one.two.three')
    'http://blog.com?hide=one.three'
    >>> url_rm_listq('hide', 'one', url='http://blog.com')
    'http://blog.com'
    """
    param = url_get_listq(key, sep=sep, url=url)
    remove = value.split(sep)
    new_params = [key for key in param if key not in remove]
    return add_or_replace_parameter(url, key, sep.join(new_params).strip(sep))


def url_add_listq(key, values:Union[str, list], url='', sep='.'):
    """
    add list member to a url query parameter

    >>> url_add_listq('hide', ['three','four'], url='http://blog.com?hide=one.two')
    'http://blog.com?hide=one.two.three.four'
    >>> url_add_listq('hide', 'three.four', url='http://localhost:5000/qa/latest-jobs.json/2?hide=&display=description')
    'http://localhost:5000/qa/latest-jobs.json/2?hide=three.four&display=description'
    >>> url_add_listq('hide', 'one', url='http://blog.com')
    'http://blog.com?hide=one'
    """
    if not url:
        url = request.url
    param = url_get_listq(key, sep=sep, url=url)
    if isinstance(values, str):
        values = values.split(sep)
    new_params = list(unique_everseen(param + values))
    return add_or_replace_parameter(url, key, sep.join(new_params).strip(sep))
