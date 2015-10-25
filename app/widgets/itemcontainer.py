from kivy.properties import ObjectProperty, NumericProperty
from widgets.layoutint import GridLayoutInt
from kivy.clock import Clock
from behaviors.queueaddwidgetbehavior import QueueAddWidgetBehavior
from widgets.stablescrollview import StableScrollView
from kivy.vector import Vector
from kivy.logger import Logger


class ItemContainer(QueueAddWidgetBehavior, GridLayoutInt):
    target = ObjectProperty()

    min_visible_widgets_num = NumericProperty(3)
    ''' Number of widgets under which texture rendering will be forced '''
    widget_update_texture_delay = NumericProperty(0.025)
    ''' Seconds delay for forcing texture rendering '''
    valid_widget_distance_screens = NumericProperty(5)
    ''' Distance from current position in which widgets should remain valid (loaded).
        The value is expressed in full screens. More distant widgets will be disposed.
    '''

    stablescrollview = ObjectProperty()
    target = ObjectProperty()
    _pending_for_capture = 0
    _child_map = None

    def __init__(self, **kwargs):
        self._pending_for_capture = 0
        self._child_map = {}
        kwargs['refresh_timer'] = kwargs.get('refresh_timer', 0)
        kwargs['widgets_per_frame'] = kwargs.get('widgets_per_frame', 1)
        super(ItemContainer, self).__init__(**kwargs)

    def enqueue(self, key, data, index=0):
        if not key:
            Logger.error('ItemContainer: enqueue() - invalid key for %s' % str(data))
            return
        elif self.widget_exists(key):
            # don't enqueue an already existing widget
            return self.get_widget(key).update_widget_data(data)
        else:
            return super(ItemContainer, self).enqueue(key, data, index)

    def get_widget_keys(self):
        return self._child_map.keys()

    def get_widget(self, key):
        return self._child_map.get(key, None)

    def widget_exists(self, key):
        return key in self._child_map

    def refresh_widgets(self, topx, topy, bottomx, bottomy, velocity, scrollobj):
        #print 'refreshing bbox %.1f %.1f %.1f %.1f' % (topx, topy, bottomx, bottomy)
        bbox = StableScrollView.BBox(topx, topy, bottomx, bottomy)
        if velocity<0:
            children = self.children
        else:
            children = reversed(self.children)
        widgets_to_delete = []
        for c in children:
            if c.collide_widget(bbox):
                if c.update_widget(data=c.data, scrollview_container=scrollobj):
                    # print 'Adding title: %s' % c.title
                    pass
            else:
                if c.dispose_widget() :
                    # print 'Removing title: %s' % c.title
                    pass
                # distance is signed
                d = c.center_y - 0.5*(topy+bottomy)
                if abs(d) > scrollobj.height*self.valid_widget_distance_screens:
                    #print 'delete title: %s' % c.data.get('key', 'unknown')
                    #widgets_to_delete.append(c)
                    pass
        # now we remove them all
        for c in widgets_to_delete:
            self.remove_widget(c)

    def _make_placeholder(self, data):
        pass

    def _produce_widget(self, key, data):
        widget = self.get_widget(key)
        if widget:
            # widget already exists
            widget.update_widget_data(data)
            return
        widget = self._make_placeholder(data)
        try:
            # force refresh at start
            if not self.children or len(self.children) < self.min_visible_widgets_num:
                def update_texture(dt):
                    widget.update_widget(scrollview_container=self.stablescrollview)
                Clock.schedule_once(update_texture, self.widget_update_texture_delay)
        except Exception as ex:
            Logger.error('ItemContainer.produce_widget(): failed to update texture: %s', ex)
        return widget

    def _duplicate_widget(self, widget):
        return self.widget_exists(getattr(widget, 'key', None))

    def clear_widgets(self, **kwargs):
        super(ItemContainer, self).clear_widgets(**kwargs)
        self._child_map = {}

    def remove_widget(self, widget, **kwargs):
        if self.stablescrollview:
            self.stablescrollview.update_container_remove(widget)
        super(ItemContainer, self).remove_widget(widget, **kwargs)
        if widget.key in self._child_map:
            del self._child_map[widget.key]

    def add_widget(self, widget, *args, **kwargs):
        # to do - make sure position is correct
        if self.stablescrollview:
            index, = args
            if index == 0:
                widget.pos[1] = self.height
            self.stablescrollview.update_container_add(widget)
        super(ItemContainer, self).add_widget(widget, *args, **kwargs)
        self._child_map[widget.key] = widget

    def _adjust_widget_width(self, widget):
        # since we're planning to capture the widget's graphics and won't add it to any container,
        # make sure widget's width is set to a concrete value and doesn't depend on the size hint
        if widget.size_hint_x is not None:
            shx = widget.size_hint_x
            widget.size_hint_x = None
            widget.width = shx * (self.width - (self.padding[0] + self.padding[2]))
            # widget.height = widget.width

    def _add_widget_impl(self, widget, index):
        self._adjust_widget_width(widget)
        super(ItemContainer, self)._add_widget_impl(widget, index)
