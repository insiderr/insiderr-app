from config import favorites_ds
from api.auth import get_auth_headers
from api import endpoint
from api.updates import get_updates_url
from modules.core.android_utils import StartNotificationsService, StopNotificationsService, GetLastNotificationMessage


def getLastNotificationMessage():
    message = GetLastNotificationMessage()
    keys = filter(None, message.split(';'))
    return keys

def startNotificationService():
    headers = get_auth_headers()
    url = endpoint('get_updates')
    keys = favorites_ds.data()
    # get system channel
    from api.streams.posts import Manager
    stream_system = None
    for s in Manager.streams:
        if s.title in ['system', 'System']:
            stream_system = s
    if stream_system:
        systemurl = endpoint('get_channel', chan_key=stream_system.key)
    else:
        systemurl = ''
    StartNotificationsService(headers, url, keys, systemurl)


def stopNotificationService():
    StopNotificationsService()
