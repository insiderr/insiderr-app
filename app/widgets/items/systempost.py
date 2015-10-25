from kivy.properties import StringProperty, NumericProperty, ListProperty
from .template import TemplateItem, ItemCallback
from .placeholder import Placeholder
from ..postbackground import PostBackground
import operator
from config import post_click_area
from behaviors.hotspotbehavior import HotSpotBehavior


class SystemPost(Placeholder):
    key = None

    def __init__(self, data, factor, target, **kwargs):
        self._take_essentials(data)
        super(SystemPost, self).__init__(data, factor, target, **kwargs)

    def _take_essentials(self, data):
        if not self.key and data:
            self.key = data.get('key', None)

    def on_width(self, *largs):
        self.height = largs[-1]

    def assign(self, widget, scrollview_container=None):
        self.key = widget.key
        super(SystemPost, self).assign(widget, scrollview_container)


class SystemPostTemplate(TemplateItem, PostBackground):
    content = StringProperty()
    button = StringProperty()
    font_color = ListProperty([1, 1, 1, 1])
    created = NumericProperty()
    _hotspots = None

    def __init__(self, **kwargs):
        super(SystemPostTemplate, self).__init__(**kwargs)

    def get_hotspots(self):
        if not self._hotspots:
            self._hotspots = []
            # self._hotspots = self.collect_hotspots(ItemCallback)
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

    def clear_widget(self):
        super(SystemPostTemplate, self).clear_widget()
        self.content = ''
        self.button = ''
        self.font_color = [1, 1, 1, 1]
        self.created = 0

    def dispose(self):
        self.clear_widget()
        super(SystemPostTemplate, self).dispose()