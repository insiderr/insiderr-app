from api import endpoint
from twisted.internet import reactor
#from twisted.web.client import Agent
from network.http_utils import Agent
from network.twisted_utils import JsonProducer, JsonReceiver, make_errback
from functools import partial
from kivy.logger import Logger


token = None


def get_auth_headers():
    if token:
        return {'Authorization': [token.encode('utf8')]}
    return {}


def _handle_register(data, on_uid, on_error):
    if 'key' in data:
        on_uid(data['key'])
    else:
        on_error('key not found in response')


def register(pub_key, on_uid, on_error=None):
    errback = on_error or make_errback()
    try:

        def handle_response(response):
            if response.code == 200:
                callback = partial(
                    _handle_register,
                    on_uid=on_uid,
                    on_error=errback)
                response.deliverBody(JsonReceiver.create(callback, errback))
            else:
                print('error %d %s -- register' % (response.code, response.phrase))
                errback('returned %s' % response.code, code=response.code)

        agent = Agent(reactor)
        d = agent.request(
            'POST',
            endpoint('register'),
            bodyProducer=JsonProducer({'pub_key': pub_key}))
        d.addCallbacks(handle_response, errback)
    except Exception as ex:
        print('error %s -- register' % ex)
        if on_error:
            errback('error %s -- register' % ex)
        else:
            errback('error %s' % ex, 'register')


def _handle_login(data, on_token, on_error):
    if 'token' in data:
        global token
        token = data['token']
        on_token(token)
    else:
        on_error('token not found in response')


def login(user_id, on_token, on_error=None):
    errback = on_error or make_errback()
    try:
        def handle_response(response):
            if response.code == 200:
                callback = partial(
                    _handle_login,
                    on_token=on_token,
                    on_error=errback)
                response.deliverBody(JsonReceiver.create(callback, errback))
            else:
                print('error %d %s -- login' % (response.code, response.phrase))
                errback('returned %s' % response.code, code=response.code)

        agent = Agent(reactor)
        d = agent.request(
            'POST',
            endpoint('login'),
            bodyProducer=JsonProducer({'key': user_id}))
        d.addCallbacks(handle_response, errback)
        timeoutCall = reactor.callLater(10, d.cancel)
        def completed(passthrough):
            print 'Login connection timeout'
            if timeoutCall.active():
                timeoutCall.cancel()

            return passthrough
        d.addBoth(completed)
    except Exception as ex:
        print('error %s -- login' % ex)
        if on_error:
            errback('error %s -- login' % ex, 'login')
        else:
            errback('error %s' % ex, 'login')
