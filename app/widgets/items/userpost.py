from kivy.properties import StringProperty, ObjectProperty, OptionProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.logger import Logger
from config import post_click_area
from .placeholder import Placeholder
from .template import TemplateItem, ItemCallback
from widgets.postbackground import PostBackground
from behaviors.hotspotbehavior import HotSpotBehavior
from theme import anonymous_nick
import operator


class UserPost(Placeholder):
    icon_set = 'dark'
    key = None
    theme = 'unknown'
    upvote_count = 0
    downvote_count = 0

    def __init__(self, data, factor, target, **kwargs):
        self._take_essentials(data)
        super(UserPost, self).__init__(data, factor, target, **kwargs)

    def _take_essentials(self, data):
        if not self.key and data:
            self.key = data.get('key', None)
        if data:
            self.upvote_count = data.get('upvote_count', 0)
            self.downvote_count = data.get('downvote_count', 0)

    def on_width(self, *largs):
        self.height = largs[-1]

    def assign(self, widget, scrollview_container=None):
        self.icon_set = widget.icon_set
        self.key = widget.key
        self.theme = widget.theme
        self.upvote_count = widget.upvote_count
        self.downvote_count = widget.downvote_count
        super(UserPost, self).assign(widget, scrollview_container)

    def update_widget(self, data=None, ignore_old_data=False, **kwargs):
        super(UserPost, self).update_widget(data, ignore_old_data, **kwargs)
        self._take_essentials(self.data)

    def update_widget_data(self, data, retries=0, ignore_old_data=False):
        super(UserPost, self).update_widget_data(data, retries, ignore_old_data)
        self._take_essentials(self.data)


class UserPostTemplate(TemplateItem, PostBackground):
    content = StringProperty()
    created = NumericProperty()
    role = StringProperty('anonymous')
    role_text = StringProperty(anonymous_nick)

    theme = StringProperty()
    attitude = OptionProperty('none', options=('like', 'dislike', 'none'))
    icon_set = OptionProperty('light', options=('light', 'dark'))

    commented = BooleanProperty(False)
    comment_count = NumericProperty(0)
    upvote_count = NumericProperty(0)
    downvote_count = NumericProperty(0)

    item_share = ObjectProperty()
    item_options = ObjectProperty()
    item_like = ObjectProperty()
    item_dislike = ObjectProperty()
    _hotspots = None

    def __init__(self, **kwargs):
        super(UserPostTemplate, self).__init__(**kwargs)

    def get_hotspots(self):
        if not self._hotspots:
            self._hotspots = self.collect_hotspots(ItemCallback)
            w, h = map(int, map(operator.mul, post_click_area, self.size))
            x, y = map(int, map(operator.sub, self.center, (w/2, h/2)))
            self._hotspots.append(
                HotSpotBehavior.make_hotspot_description(
                    'item_click',
                    [x, y, w, h],
                    allow_expand=False))
        return self._hotspots

    def set_load_callback(self, cb, *args):
        if self.color and not self.image:
            return False
        elif self.image_widget and self.image:
            self.image_widget.SetLoadCallback(cb, args)
            return True
        return False

    def dispose(self):
        self.clear_widget()
        super(UserPostTemplate, self).dispose()
