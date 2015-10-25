from api import endpoint
from api.helpers.post import post as post_helper
from api.helpers.delete import delete as delete_helper


def post_up(item_key, on_voted=None, on_error=None):
    post_helper(
        endpoint('post_voteup', item_key=item_key),
        None,
        on_voted,
        on_error)

def delete_up(item_key, on_deleted=None, on_error=None):
    delete_helper(
        endpoint('delete_voteup', item_key=item_key),
        on_deleted,
        on_error)

def post_down(item_key, on_voted=None, on_error=None):
    post_helper(
        endpoint('post_votedown', item_key=item_key),
        None,
        on_voted,
        on_error)

def delete_down(item_key, on_deleted=None, on_error=None):
    delete_helper(
        endpoint('delete_votedown', item_key=item_key),
        on_deleted,
        on_error)