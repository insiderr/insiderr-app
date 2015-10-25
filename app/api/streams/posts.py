from kivy.event import EventDispatcher
from kivy.logger import Logger
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from . import Stream
from utilities.unicode import convert_json_from_unicode
from api.channels import get_channel, get_channels


class PostsStream(Stream):
    key = StringProperty()
    title = StringProperty()

    def _do_get_page(self, on_page, on_error, **kwargs):
        get_channel(chan_key=self.key, on_page=on_page, on_error=on_error, **kwargs)


class PostsManager(EventDispatcher):
    logged_in = BooleanProperty(False)
    connected = BooleanProperty(False)
    streams = ListProperty([])

    #TODO: handle network disconnect (turn off 'logged_in' and 'connected')

    def on_logged_in(self, instance, value):
        if value:
            get_channels(on_channels=self._handle_channels)
        else:
            self.connected = False

    def _handle_channels(self, data):
        data = convert_json_from_unicode(data)
        self.streams = [PostsStream(manager=self, **chan_data) for chan_data in data]
        self.connected = True
        Logger.info('PostsManager: connected. channels=%s' % ([s.title for s in self.streams]))


Manager = PostsManager()