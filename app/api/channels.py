from api import endpoint
from api.helpers.get import get as get_helper
from api.helpers.page import get_page_args, get as get_page
from functools import partial


def _handle_channels(data, on_channels, on_error):
    if 'channels' in data:
        on_channels(data['channels'])
    elif on_error:
        on_error('channels not found in response')


def get_channels(on_channels, on_error=None):
    get_helper(
        url=endpoint('get_channels'),
        on_response=partial(_handle_channels, on_channels=on_channels, on_error=on_error),
        on_error=on_error)


def get_channel(chan_key, on_page, on_error=None, **kwargs):
    get_page(
        url=endpoint('get_channel', chan_key=chan_key),
        page_args=get_page_args(**kwargs),
        response_key='updates',
        on_page=on_page,
        on_error=on_error)
