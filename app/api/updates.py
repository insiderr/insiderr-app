from . import endpoint, add_params
from .helpers.get import get as get_helper
from functools import partial
from network.twisted_utils import make_errback


def _handle_updates(data, on_updates, on_error):
    if 'updates' in data:
        on_updates(data['updates'], hash=data.get('hash', None))
    elif on_error:
        on_error('updates not found in response')


def get_updates_url(keys, hash=None):
    kwargs = {'key': keys}
    if hash:
        kwargs['hash'] = hash
    return add_params(
        endpoint('get_updates'),
        allow_multiple=True,
        **kwargs)


def get(keys, on_updates, on_error=None, hash=None):
    errback = on_error or make_errback()
    get_helper(
        url=get_updates_url(keys, hash),
        on_response=partial(_handle_updates, on_updates=on_updates, on_error=errback),
        on_error=on_error)

