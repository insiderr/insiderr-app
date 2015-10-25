from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import ContentDecoderAgent, GzipDecoder
from twisted.web.http_headers import Headers
import twisted.web.client
from kivy.logger import Logger

if twisted.version.major < 14:
    print 'TWISTED -- %s' % str(twisted.version)
    from twisted.web.client import Agent as TwistedAgent
    class Agent(TwistedAgent):
        def __init__(self, reactor, **kwargs):
            super(Agent, self).__init__(reactor, **kwargs)
else:
    print 'TWISTED -- %s' % str(twisted.version)
    from twisted.web.client import WebClientContextFactory, WebClientContextFactory, CertificateOptions, platformTrust
    from twisted.web.client import Agent as TwistedAgent
    from OpenSSL import SSL

    class ClientContextFactory(WebClientContextFactory):
        """A context factory for SSL clients."""
        isClient = 1
        # SSLv23_METHOD allows SSLv2, SSLv3, and TLSv1.  We disable SSLv2 and SSLv3 below,
        method = SSL.SSLv3_METHOD

        _contextFactory = SSL.Context

        def _getCertificateOptions(self, hostname, port):
            return CertificateOptions(
                method=SSL.SSLv3_METHOD,
                trustRoot=platformTrust()
            )

        def callbackVerfiy(self, *largs):
            pass

        def getContext(self, hostname, port):
            ctx = self._getCertificateOptions(hostname, port).getContext()
            OP_NO_TLSv1_2 = int('0x10000000',16)
            OP_NO_TLSv1_1 = int('0x08000000',16)
            ctx.set_options(OP_NO_TLSv1_2)
            ctx.set_options(OP_NO_TLSv1_1)
            #ctx.set_options(SSL.OP_NO_TLSv1)
            ctx.set_options(SSL.OP_NO_SSLv3)
            ctx.set_options(SSL.OP_NO_SSLv2)
            ctx.set_verify(SSL.VERIFY_NONE, self.callbackVerfiy)
            return ctx

    class Agent(TwistedAgent):
        def __init__(self, reactor, **kwargs):
            kwargs['contextFactory'] = ClientContextFactory()
            super(Agent, self).__init__(reactor, **kwargs)


class StringReceiver(Protocol):
    buffer = ""

    def __init__(self, deferred=None):
        self._deferred = deferred

    def dataReceived(self, data):
        self.buffer += data

    def connectionLost(self, reason):
        if self._deferred and reason.check(twisted.web.client.ResponseDone):
            self._deferred.callback(self.buffer)
        else:
            self._deferred.errback(self.buffer)


class BodyReciever(Protocol):
    data = []
    def __init__(self, finished, cbGotIt):
        self.finished = finished
        self.cbGotIt = cbGotIt

    def dataReceived(self, bytes):
        self.data.append(bytes)

    def connectionLost(self, reason):
        #pdb.set_trace()
        print 'Finished receiving body:', reason.getErrorMessage()
        isDone = reason.check(twisted.web.client.ResponseDone) is not None
        isDone = len(self.data)>0
        if(isDone):
            self.cbGotIt(''.join(self.data))
        else:
            print "error!"
        self.finished.callback(None)

def url_open_async(url, callback):
    print "request"
    agent = Agent(reactor)
    d = agent.request(
        'GET',
        url,
        Headers({'User-Agent': ['Twisted Web Client Example']}),
        None)

    def cbRequest(response):
        finished = Deferred()
        response.deliverBody(BodyReciever(finished, callback))
        return finished

    d.addCallback(cbRequest)

    def cbShutdown(ignored):
        pass
    #    reactor.stop()

    d.addBoth(cbShutdown)

from twisted.web.client import getPage

def url_open_async_simple(url, callback):
    pageFetchedDeferred = getPage(url)
    pageFetchedDeferred.addCallback(callback)
    pageFetchedDeferred.addErrback(callback)

def url_upload_file_async(url, file, callback):
    agent = Agent(reactor)
    body = twisted.web.client.FileBodyProducer(file)
    d = agent.request(
        'POST',
        url,
        Headers({'User-Agent': ['Twisted Web Client Example'],
                 'Content-Type': ['application/octet-stream']}),
        body)

    def cbRequest(response):
        finished = Deferred()
        response.deliverBody(BodyReciever(finished, callback))
        return finished

    def errorBack(ignored):
        Logger.error('Problem uploading file')

    d.addCallbacks(cbRequest, errorBack)

from multipart_producer import MultiPartProducer
def url_upload_data_async(url, files={}, data={}, progressCallback=None, doneCallback=None):

    def produce_finished(data):
        print 'produce finished',data
    def produce_error(error):
        print 'produce error', error

    producerDeferred = Deferred()
    producerDeferred.addCallback(produce_finished)
    producerDeferred.addErrback(produce_error)

    def receive_finished(data):
        print 'recieve finished', data
        doneCallback(data)

    def receive_error(error):
        Logger.error('Problem uploading file')
        print 'recieve error', error

    receiverDeferred = Deferred()
    receiverDeferred.addCallback(receive_finished)
    receiverDeferred.addErrback(receive_error)

    producer = MultiPartProducer(files, data, progressCallback, producerDeferred)
    receiver = StringReceiver(receiverDeferred)

    agent = Agent(reactor)
    headers = Headers({'User-Agent': ['Twisted Web Client Example']})
    headers.addRawHeader("Content-Type", "multipart/form-data; boundary=%s" % producer.boundary)

    requestDeffered = agent.request('POST', url, headers, producer)
    requestDeffered.addCallback(lambda response: response.deliverBody(receiver))


def request_gzipped_url(url, callback, errback=None, timeout=None, **kwargs):
    ''' Get URL with gzip-decoder support. '''
    agent = ContentDecoderAgent(Agent(reactor), [('gzip', GzipDecoder)])
    d = agent.request(
        'GET',
        url,
        Headers({'User-Agent': ['gzip']}))

    def handleResponse(response, **kwargs):
        receiverDeferred = Deferred()
        receiverDeferred.addCallback(callback, **kwargs)
        receiver = StringReceiver(receiverDeferred)
        response.deliverBody(receiver)

    if timeout:
        timeoutCall = reactor.callLater(timeout, d.cancel)

        def completed(passthrough):
            if timeoutCall.active():
                timeoutCall.cancel()
            return passthrough
        d.addBoth(completed)

    d.addCallback(handleResponse, **kwargs)
    if errback:
        d.addErrback(errback, **kwargs)
    return d


