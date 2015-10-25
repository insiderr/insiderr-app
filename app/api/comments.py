from api import endpoint
from api.helpers.post import post as post_helper
from api.helpers.page import get_page_args, get as get_page


def post(post_key, content, role, role_text, on_created=None, on_error=None):
    post_helper(
        endpoint('post_comment', post_key=post_key),
        {'content': content, 'role': role, 'role_text': role_text},
        on_created,
        on_error)


def get_comments(post_key, on_page, on_error=None, **kwargs):
    get_page(
        url=endpoint('get_comments', post_key=post_key),
        page_args=get_page_args(**kwargs),
        response_key='comments',
        on_page=on_page,
        on_error=on_error)
