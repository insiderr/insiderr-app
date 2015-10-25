from kivy.logger import Logger
from twisted.internet.protocol import Protocol, connectionDone
from twisted.internet.defer import Deferred, succeed
from twisted.web.iweb import IBodyProducer
from zope.interface import implements
import json
from functools import partial

def _log_error(failure, context='twisted', code=None, debug=True):
    Logger.error('%s: %s' % (context, failure))
    if debug and hasattr(failure, 'value') and hasattr(failure.value, 'reasons'):
        failure.value.reasons[0].printTraceback()

def make_errback(frames_back=1):
    # way too mcuh time to create the object!
    # return simple error function
    return _log_error
    # import inspect
    # frm = inspect.stack()[frames_back]
    # func = frm[3]
    # mod = inspect.getmodule(frm[0])
    # return partial(_log_error, context='{}.{}'.format(mod.__name__ if mod else '', func))


class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class JsonProducer(StringProducer):
    def __init__(self, data):
        super(JsonProducer, self).__init__(json.dumps(data))


class JsonReceiver(Protocol):
    buffer = ""

    def __init__(self, deferred=None):
        self._deferred = deferred

    @staticmethod
    def create(callback=None, errback=None):
        rd = Deferred()
        rd.addCallbacks(callback, errback)
        return JsonReceiver(rd)

    def getResult(self):
        return json.loads(self.buffer)

    def dataReceived(self, data):
        self.buffer += data

    def connectionLost(self, reason=connectionDone):
        if not self._deferred:
            return
        try:
            self._deferred.callback(self.getResult())
        except:
            self._deferred.errback(self.buffer)

