from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ObjectProperty, OptionProperty, BooleanProperty,\
    ListProperty, NumericProperty
from widgets.items.template import TemplateItem
from widgets.layoutint import GridLayoutInt
from widgets.items.placeholder import Placeholder
from behaviors.hotspotbehavior import HotSpotBehavior
from copy import copy


class UserPostFav(Placeholder):
    theme = 'unknown'
    key = 'unknown'
    changed = False
    time = None

    def __init__(self, data, factor, target, **kwargs):
        self.key = data.get('key', None)
        self.time = data.get('time', None)
        self.changed = data.get('changed', False)
        super(UserPostFav, self).__init__(data, factor, target, **kwargs)

    def assign(self, widget, scrollview_container=None):
        self.theme = widget.theme
        self.key = widget.key
        self.changed = widget.changed
        super(UserPostFav, self).assign(widget, scrollview_container)

    def set_changed(self, changed):
        self.update_widget_data({'changed': changed})

    def update_widget_data(self, data, retries=0, ignore_old_data=False):
        self.changed = data.get('changed', False)
        super(UserPostFav, self).update_widget_data(data, retries, ignore_old_data)


class UserPostFavTemplate(TemplateItem, FloatLayout):
    notifications_container = ObjectProperty()
    content = StringProperty()
    theme = StringProperty()
    key = StringProperty()
    icon_set = OptionProperty('light', options=('light', 'dark'))
    changed = BooleanProperty(False)
    color = ListProperty([0, 0, 0, 0])
    shadow_color = ListProperty()

    _hotspots = []

    def __init__(self, **kwargs):
        super(UserPostFavTemplate, self).__init__(**kwargs)
        self.add_notifications(kwargs)

    def update(self, data):
        super(UserPostFavTemplate, self).update(data)
        self.add_notifications(data)

    def add_notifications(self, data):
        if self.changed:
            self.add_notification(data.get('upvote_count', 0), key='like')
            self.add_notification(data.get('downvote_count', 0), key='dislike')
            self.add_notification(data.get('comment_count', 0), key='comment')

    def add_notification(self, count, key):
        self.notifications_container.add_widget(
            UserPostFavNotification(
                key=key,
                count=count,
                icon_set=self.icon_set))

    def get_hotspots(self):
        if not self._hotspots:
            # self._hotspots = self.collect_hotspots(ItemCallback)
            self._hotspots.append(
                HotSpotBehavior.make_hotspot_description(
                    'item_click',
                    self.pos + self.size,
                    allow_expand=False))
        return self._hotspots

    def set_load_callback(self, cb, *args):
        return False

    def dispose(self):
        self.notifications_container.clear_widgets()
        super(UserPostFavTemplate, self).dispose()


class UserPostFavNotification(GridLayoutInt):
    key = OptionProperty('like', options=('like', 'dislike', 'comment'))
    icon_set = OptionProperty('light', options=('light', 'dark'))
    count = NumericProperty(0)
