from twisted.internet import reactor
from twisted.web.client import HTTPConnectionPool, ContentDecoderAgent, GzipDecoder
from network.http_utils import Agent
from twisted.web.http_headers import Headers
from network.twisted_utils import JsonProducer, JsonReceiver, make_errback
from api.auth import get_auth_headers

pool = HTTPConnectionPool(reactor)
pool.maxPersistentPerHost = 30


def get(url, data=None, on_response=None, on_error=None):
    errback = on_error or make_errback(frames_back=2)
    try:
        def handle_response(response):
            if response.code == 200:
                response.deliverBody(JsonReceiver.create(on_response, errback))
            else:
                errback('returned %s' % response.code)

        agent = ContentDecoderAgent(Agent(reactor, pool=pool), [('gzip', GzipDecoder)])
        headers = Headers(get_auth_headers())
        headers.addRawHeader('User-Agent', 'gzip')
        d = agent.request(
            'GET',
            url,
            headers=headers,
            bodyProducer=JsonProducer(data) if data else None)
        d.addCallbacks(handle_response, errback)
    except Exception as ex:
        errback('error %s' % ex)