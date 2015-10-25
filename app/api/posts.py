from api import endpoint
from api.helpers.post import post as post_helper
from api.helpers.get import get as get_helper
from functools import partial
from utilities.unicode import convert_json_from_unicode


def post(content, role, role_text, theme, background, channels, on_created=None, on_error=None):
    args = {
        'content': content,
        'role': role,
        'role_text': role_text,
        'theme': theme,
        'background': background,
        'channels': channels or []
    }
    post_helper(
        url=endpoint('post_post'),
        data=args,
        on_created=on_created,
        on_error=on_error)


def _handle_post(data, on_post, on_error):
    if 'post' in data:
        on_post(convert_json_from_unicode(data['post']))
    elif on_error:
        on_error('post not found in response')


def get(post_key, on_post, on_error=None):
    get_helper(
        endpoint('get_post', post_key=post_key),
        on_response=partial(_handle_post, on_post=on_post, on_error=on_error),
        on_error=on_error)