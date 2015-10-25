from kivy.properties import StringProperty
from . import Stream
from api.comments import get_comments


class CommentsStream(Stream):
    post_key = StringProperty()

    def __init__(self, **kwargs):
        super(CommentsStream, self).__init__(manager=None, **kwargs)

    def _do_get_page(self, on_page, on_error, **kwargs):
        get_comments(post_key=self.post_key, on_page=on_page, on_error=on_error, **kwargs)
