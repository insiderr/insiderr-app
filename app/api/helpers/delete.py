from twisted.internet import reactor
#from twisted.web.client import Agent
from network.http_utils import Agent
from twisted.web.http_headers import Headers
from network.twisted_utils import JsonProducer, JsonReceiver, make_errback
from api import add_params
from api.auth import get_auth_headers
from functools import partial
from uuid import uuid4


def _handle_delete(data, on_created, on_error):
    if 'key' not in data:
        on_error('key not found in response (%s)' % str(data))
    elif on_created:
        on_created(**data)


def delete(url, on_created=None, on_error=None):
    errback = on_error or make_errback(frames_back=2)
    try:
        def handle_response(response):
            if response.code == 200:
                callback = partial(
                    _handle_delete,
                    on_created=on_created,
                    on_error=errback)
                response.deliverBody(JsonReceiver.create(callback, errback))
            else:
                errback('returned %s' % response.code)
        agent = Agent(reactor)
        headers = Headers(get_auth_headers())
        d = agent.request(
            'DELETE',
            add_params(url, rid=uuid4().hex),
            headers=headers)
        d.addCallbacks(handle_response, errback)
    except Exception as ex:
        errback('error %s' % ex)
