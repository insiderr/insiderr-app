from kivy.uix.behaviors import ButtonBehavior
from inspect import getmembers, ismethod
from copy import copy
import operator


class HotSpotCallback(object):
    _hotspot_keys = None

    @classmethod
    def get_hotspot_keys(cls):
        if not cls._hotspot_keys:
            cls._hotspot_keys = [k for k, _ in getmembers(cls, predicate=ismethod)]
        return cls._hotspot_keys


class HotSpotBehavior(ButtonBehavior):
    rect_expand_factor = 2.0
    # each item in least is a tuple of :
    # [key, callback_func, [x,y,w,h], args, kwargs]
    # called with callback_func(touch, *args, **kwargs)
    hotspots = None
    _hotspots_desc = None

    def __init__(self, **kwargs):
        self.register_event_type('on_hotspots_attached')
        super(HotSpotBehavior, self).__init__(**kwargs)
        self.clear_hotspots()

    def clear_hotspots(self):
        self.hotspots = []

    def attach_hotspots_from(self, other, target, instance=None, override_only=[], dont_override=[]):
        assert isinstance(other, HotSpotBehavior)
        desc = other._hotspots_desc
        if override_only:
            # In case we need to keep some hotspots attached to the other target,
            # filter out the description for these hotspots and initialize
            # our hotspots with the other hotspots. attach_hotspots() will override
            # the hotspots we won't be keeping.
            desc = [d for d in desc if d[0] in override_only]
            self.hotspots = copy(other.hotspots)
        if dont_override:
            desc = [d for d in desc if d[0] not in dont_override]
        self.attach_hotspots(target, desc, instance=instance, clear=not override_only)

    @staticmethod
    def collide_rect(x, y, rect_x, rect_y, rect_w, rect_h):
        return ((rect_x <= x <= rect_x + rect_w)
                and (rect_y <= y <= rect_y + rect_h))

    def find_hotspot_touch(self, touch):
        # key, instance, cbfunc, rect, args, kwargs
        for spot in self.hotspots:
            rect = spot[3]
            if HotSpotBehavior.collide_rect(
                    *touch.pos,
                    rect_x=rect[0] + self.x,
                    rect_y=rect[1] + self.y,
                    rect_w=rect[2],
                    rect_h=rect[3]):
                return spot
        return None

    def call_on_release(self, touch):
        spot = self.find_hotspot_touch(touch)
        if spot:
            key, instance, cbfunc, rect, args, kwargs = spot
            cbfunc(instance, touch, *args, **kwargs)
            return True
        return False

    def _expand_rect(self, rect):
        x, y, w, h = rect
        ew = int(w * self.rect_expand_factor)
        eh = int(h * self.rect_expand_factor)
        ex = max(0, x - int(abs(ew - w) / 2))
        ey = max(0, y - int(abs(eh - h) / 2))
        return ex, ey, ew, eh

    def remove_hotspot(self, key):
        keys = [hs[0] for hs in self.hotspots]
        if key in keys:
            self.hotspots.pop(keys.index(key))

    def add_hotspot(self, key, instance, func, rect, *args, **kwargs):
        keys = [hs[0] for hs in self.hotspots]
        if key in keys:
            if not instance:
                instance = self.hotspots[keys.index(key)][1]
            entry = (key, instance, func, rect, args, kwargs)
            self.hotspots[keys.index(key)] = entry
        else:
            if not instance:
                instance = self
            entry = (key, instance, func, rect, args, kwargs)
            self.hotspots.append(entry)

    @staticmethod
    def make_hotspot_description(key, rect, allow_expand=True):
        return (key, rect, allow_expand)

    def attach_hotspots(self, target, hotspots_desc, instance = None, clear=True):
        if clear:
            self.clear_hotspots()
        self._hotspots_desc = hotspots_desc
        if hotspots_desc:
            for key, rect, allow_expand in hotspots_desc:
                func = getattr(target, key, None)
                if func:
                    if allow_expand:
                        rect = self._expand_rect(rect)
                    self.add_hotspot(key, instance, func, rect)
        self.dispatch('on_hotspots_attached')

    def on_hotspots_attached(self):
        pass

    def on_touch_up(self, touch):
        return super(HotSpotBehavior, self).on_touch_up(touch)

    def on_touch_down(self, touch):
        if super(ButtonBehavior, self).on_touch_down(touch):
            return True
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False
        if not self.call_on_release(touch):
            return False
        touch.grab(self)
        touch.ud[self] = True
        self.last_touch = touch
        self._do_press()
        self.dispatch('on_press')
        return True
