from .placeholder import Placeholder
from .template import TemplateItem, ItemCallback
from widgets.layoutint import GridLayoutInt
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, AliasProperty, OptionProperty
from utilities.formatting import get_formatted_when
from kivy.logger import Logger


class Comment(Placeholder):
    key = None
    theme = 'unknown'
    icon = 'unknown'
    time = None
    upvote_count = 0
    downvote_count = 0

    def __init__(self, data, factor, target, **kwargs):
        self.key = data.get('key', None)
        self._take_essentials(data)
        super(Comment, self).__init__(data, factor, target, **kwargs)

    def _take_essentials(self, data):
        if not self.key and data:
            self.key = data.get('key', None)
        if data:
            self.time = data.get('time', None)
            self.theme = data.get('theme', 'unknown')
            self.icon = data.get('icon', 'unknown')
            self.upvote_count = data.get('upvote_count', 0)
            self.downvote_count = data.get('downvote_count', 0)

    def assign(self, widget, scrollview_container=None):
        self.key = widget.key
        self.theme = widget.theme
        self.icon = widget.icon
        self.time = widget.time
        self.upvote_count = widget.upvote_count
        self.downvote_count = widget.downvote_count
        super(Comment, self).assign(widget, scrollview_container)

    def update_widget(self, data=None, ignore_old_data=False, **kwargs):
        ret = super(Comment, self).update_widget(data, ignore_old_data, **kwargs)
        self._take_essentials(self.data)
        return ret

    def update_widget_data(self, data, retries=0, ignore_old_data=False):
        ret = super(Comment, self).update_widget_data(data, retries, ignore_old_data)
        self._take_essentials(self.data)
        return ret

class CommentTemplate(TemplateItem, GridLayoutInt):
    icon_widget = ObjectProperty()
    icon = StringProperty()
    icon_color = StringProperty('FFFFFFFF')
    content = StringProperty()
    role = StringProperty()
    role_text = StringProperty()
    time = NumericProperty()
    theme = StringProperty()
    upvote_count = NumericProperty(0)
    downvote_count = NumericProperty(0)

    attitude = OptionProperty('none', options=('like', 'dislike', 'none'))

    item_like = ObjectProperty()
    item_dislike = ObjectProperty()

    _hotspots = None

    def get_formatted_time(self):
        return get_formatted_when(self.time, absolute_time=False)

    formatted_time = AliasProperty(get_formatted_time, None, bind=('time',))

    def __init__(self, **kwargs):
        super(CommentTemplate, self).__init__(**kwargs)

    def get_hotspots(self):
        if not self._hotspots:
            self._hotspots = self.collect_hotspots(ItemCallback)
        return self._hotspots

    def set_load_callback(self, cb, *args):
        return False

    def dispose(self):
        self.time = 0
        self.icon = ''
        self.content = ''
        self.role = ''
        self.theme = ''
        self.upvote_count = 0
        self.downvote_count = 0
        self.attitude = 'none'
        super(CommentTemplate, self).dispose()
