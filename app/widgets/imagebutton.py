from kivy.properties import BooleanProperty, StringProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.logger import Logger
from theme import default_font_name
from kivy.animation import Animation
from kivy.clock import Clock


class ImageCollideBehavior(object):
    hit_test = BooleanProperty(False)
    background_normal = StringProperty()
    background_down = StringProperty()

    def get_core_image(self):
        pass

    def collide_point(self, x, y):
        if super(ImageCollideBehavior, self).collide_point(x, y):
            if not self.hit_test:
                return True
            ci = self.get_core_image()
            if not ci.image:
                Logger.warning('ImageButtonBase: no image data for %s (note - hit testing doesn''t work for atlas images)' % self.source)
                return True
            x = int(float(x - self.x) / self.width * (ci.image._data[0].width - 1))
            y = int((1 - float(y - self.y) / self.height) * (ci.image._data[0].height - 1))
            r, g, b, a = ci.read_pixel(x, y)
            return a > 0
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(ImageCollideBehavior, self).on_touch_up(touch)
        assert(self in touch.ud)
        touch.ungrab(self)
        self.last_touch = touch
        self._do_release()
        if self.collide_point(touch.x, touch.y):
            self.dispatch('on_release')
        return True


class ImageButtonBase(ButtonBehavior, Image):
    def get_core_image(self):
        return self._coreimage


class ImageButton(ImageCollideBehavior, ImageButtonBase):
    pass


class ImageToggleButtonBase(ToggleButtonBehavior, RelativeLayout):
    theimage = ObjectProperty()
    thelabel = ObjectProperty()
    title = StringProperty()
    font_size = NumericProperty(12)
    font_name = StringProperty(default_font_name)
    color_normal = ListProperty([1, 1, 1, 1])
    color_down = ListProperty([0, 0, 0, 1])
    color_disabled = ListProperty([.5, .5, .5, 1])
    bottom_spacing = NumericProperty(0)
    bottom_spacing_active_extra = NumericProperty(10)
    move_up_duration = NumericProperty(.8)
    move_down_duration = NumericProperty(.2)
    show_label_timeout = NumericProperty(1)
    hide_label_duration = NumericProperty(.4)
    transition = StringProperty('out_bounce')
    hide_label = BooleanProperty(True)

    def _show_label(self, *args):
        a = Animation(opacity=1, d=self.move_up_duration/2)
        a.bind(on_complete=self._trigger_hide_label)
        a.start(self.thelabel)

    def _trigger_hide_label(self, *args):
        if self.hide_label:
            Clock.schedule_once(self._hide_label, self.show_label_timeout)

    def _hide_label(self, *args):
        Animation(opacity=0, d=self.hide_label_duration).start(self.thelabel)

    def _move_completed(self, *args):
        pass

    def on_state(self, instance, value):
        Animation.cancel_all(self)
        Animation.cancel_all(self.thelabel)
        Clock.unschedule(self._show_label)
        Clock.unschedule(self._hide_label)
        Clock.unschedule(self._trigger_hide_label)
        if value == 'down':
            bs = self.thelabel.height + self.bottom_spacing_active_extra
            d = self.move_up_duration
            a = Animation(bottom_spacing=bs, d=d, t=self.transition)
            a.bind(on_complete=self._move_completed)
            a.start(self)
            Clock.schedule_once(self._show_label, d/2)
        else:
            Animation(bottom_spacing=0, d=self.move_down_duration).start(self)
            self.thelabel.opacity = 0


class ImageToggleButton(ImageCollideBehavior, ImageToggleButtonBase):
    def get_core_image(self):
        if self.theimage:
            return self.theimage._coreimage
