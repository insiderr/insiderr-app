from network.twisted_utils import make_errback
from ..helpers.get import get as get_helper
from functools import partial
from urllib import urlencode
from urlparse import urlparse, urlunparse


def get_page_args(count=None, hash=None, fields=None, **kwargs):
    args = {}
    if hash:
        args['hash'] = hash
    if count:
        args['count'] = count
    if fields:
        args['fields'] = fields
    return args


def _handle_get_page(data, response_key, on_page, on_error):
    if response_key in data:
        on_page(data[response_key], hash=data.get('hash', None))
    elif on_error:
        on_error('%s not found in response' % response_key)


def get(url, page_args, response_key, on_page, on_error=None):
    errback = on_error or make_errback(frames_back=2)
    url_parts = list(urlparse(url))
    url_parts[4] = urlencode(page_args, doseq=True)
    get_helper(
        url=urlunparse(url_parts),
        on_response=partial(_handle_get_page, response_key=response_key, on_page=on_page, on_error=errback),
        on_error=errback)