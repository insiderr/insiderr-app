from functools import partial
from api.votes import post_up as post_vote_up, post_down as post_vote_down, \
    delete_up as delete_vote_up, delete_down as delete_vote_down
from modules.core.android_utils import LogTestFairy, Toast
from config import attitude_ds
from kivy.logger import Logger


_params = {
    'like': [delete_vote_up, post_vote_up, 'upvote_count', 'downvote_count'],
    'dislike': [delete_vote_down, post_vote_down, 'downvote_count', 'upvote_count']
}


def item_vote(item, attitude, update_func, testfairy_prefix, **kwargs):
    if attitude not in _params:
        return

    del_vote, post_vote, pos_field, neg_field = _params[attitude]

    key = item.key
    update_func = partial(update_func, key=key)
    pos_value = getattr(item, pos_field, 0)
    neg_value = getattr(item, neg_field, 0)
    last_attitude = attitude_ds.query(lambda ds: ds.get(key, 'None'))

    def on_network_error(*largs):
        print 'Network Error %s' % str(*largs)
        Logger.info('item_vote: failed voting (network error)')
        Toast('Voting failed (no network access)')

    if last_attitude == attitude:
        # delete existing attitude
        LogTestFairy('{} item delete {}'.format(testfairy_prefix, attitude))
        d = {pos_field: max(0, pos_value - 1)}
        update_func(attitude='none', **d)
        del_vote(
            item_key=key,
            on_error=on_network_error)
    else:
        # change attitude
        LogTestFairy('{} item {}'.format(testfairy_prefix, attitude))
        d = {pos_field: pos_value + 1}
        if last_attitude in _params:
            # previous attitude is not none, decrement opposite value
            d[neg_field] = max(0, neg_value - 1)
        update_func(attitude=attitude, **d)
        post_vote(
            item_key=key,
            on_error=on_network_error)
