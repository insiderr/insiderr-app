from api import endpoint
from api.helpers.post import post as post_helper


def post(content, on_created=None, on_error=None):
    post_helper(
        endpoint('post_feedback'),
        data=content,
        on_created=on_created,
        on_error=on_error)
