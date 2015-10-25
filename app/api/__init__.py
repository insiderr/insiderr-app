from config import base_url
from urllib import urlencode
from urlparse import urlparse, urlunparse

endpoints = {
    # Authentication
    'register': '{base_url}/register/',
    'login': '{base_url}/login/',

    # Channels
    'get_channels': '{base_url}/channels/',
    'get_channel': '{base_url}/channels/{chan_key}',

    # Posts
    'get_post': '{base_url}/posts/{post_key}',
    'post_post': '{base_url}/posts/',

    # Comments
    'get_comments': '{base_url}/comments/{post_key}',
    'post_comment': '{base_url}/comments/{post_key}',

    # Voting
    'post_voteup': '{base_url}/votes/{item_key}/up',
    'delete_voteup': '{base_url}/votes/{item_key}/up',
    'post_votedown': '{base_url}/votes/{item_key}/down',
    'delete_votedown': '{base_url}/votes/{item_key}/down',

    # Updates
    'get_updates': '{base_url}/updates/',

    # Flags
    'post_flag': '{base_url}/flag/{post_key}',

    # Feedbacks
    'post_feedback': '{base_url}/feedbacks/',

    # Items
    'get_items': '{base_url}/items/',
}


base_ip = None


def resolve_base_url(on_resolved):
    global base_ip
    if base_ip:
        on_resolved(base_ip)
        return
    import twisted.names.client
    from urlparse import urlparse, urlunparse
    domain = urlparse(base_url).hostname
    def update_base_ip(result):
        global base_ip
        if isinstance(result, basestring):
            base_ip = base_url.replace(domain, result)
        else:
            # we failed - just use the original url - maybe it has ip anyhow
            base_ip = base_url
        on_resolved(base_ip)
    d = twisted.names.client.getHostByName(domain, timeout=2)
    d.addBoth(update_base_ip)
    d.addErrback(update_base_ip)


def add_params(url, allow_multiple=False, **kwargs):
    url_parts = list(urlparse(url))
    url_parts[4] = urlencode(kwargs, doseq=allow_multiple)
    return urlunparse(url_parts)


def endpoint(endpoint_key, params=None, **kwargs):
    url = endpoints[endpoint_key].format(
        base_url=base_ip,
        **kwargs)
    return url
