from api import endpoint
from api.helpers.post import post as post_helper


def post(post_key, on_created=None, on_error=None):
    post_helper(
        endpoint('post_flag', post_key=post_key),
        on_created=on_created,
        on_error=on_error)
