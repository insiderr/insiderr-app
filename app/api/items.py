from network.twisted_utils import make_errback
from api import endpoint, add_params
from api.helpers.get import get as get_helper
from functools import partial
from utilities.unicode import convert_json_from_unicode


def _handle_items(data, on_items, on_error):
    if 'objects' in data:
        on_items(
            convert_json_from_unicode(data['objects']),
            hash=data.get('hash', None))
    elif on_error:
        on_error('post not found in response')


def get(keys, on_items, on_error=None, **kwargs):
    get_helper(
        url=add_params(endpoint('get_items'), key=keys, allow_multiple=True),
        on_response=partial(_handle_items, on_items=on_items, on_error=on_error),
        on_error=on_error)

