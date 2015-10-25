from twisted.internet import reactor
from network.http_utils import Agent
from network.twisted_utils import StringProducer
from kivy.logger import Logger
from urllib import urlencode
from config import google_analytics_ds
from uuid import uuid4
from twisted.web.http_headers import Headers

#url = 'http://www.google-analytics.com/collect'
url = 'https://ssl.google-analytics.com/collect'

tracking_id = '##some_tracking_id##'
client_id = google_analytics_ds.query(lambda ds: ds.get('client_id'))

if not client_id:
    client_id = str(uuid4())
    def update(ds):
        ds['client_id'] = client_id
    google_analytics_ds.update(update)


def post(text):
    try:
        def handle_response(response):
            if not hasattr(response, 'code'):
                Logger.warning('google_analytics.post(): got %s' % (str(response)))
                return
            if response.code / 100 != 2:
                Logger.warning('google_analytics.post(): got %s: %s' % (response.code, response))

        from config import app_version, app_platform
        text_lower = text.lower()
        if 'screen' in text_lower and 'exit' not in text_lower:
            body = urlencode({
                'v': '1',
                'tid': tracking_id,
                'cid': client_id,
                'ds': 'app',
                't': 'screenview',
                'an': 'Insiderr',
                'aid': 'com.insiderr.app.%s' % app_platform,
                'av': str(app_version),
                'cd': text,
            })
        else:
            body = urlencode({
                'v': '1',
                'tid': tracking_id,
                'cid': client_id,
                'ds': 'app',
                't': 'event',
                'an': 'Insiderr',
                'aid': 'com.insiderr.app.%s' % app_platform,
                'av': str(app_version),
                'ec': 'debug-%s' % app_platform, #category
                'ea': text,
                #'el': 'label',
            })

        agent = Agent(reactor)
        headers = Headers()
        #headers.addRawHeader('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36')
        d = agent.request(
            method='POST',
            uri=url,
            headers=headers,
            bodyProducer=StringProducer(body))
        d.addBoth(handle_response)
    except Exception as ex:
        Logger.error('google_analytics.post(): exception %s' % ex)

