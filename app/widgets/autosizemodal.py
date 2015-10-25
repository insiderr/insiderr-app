from kivy.uix.modalview import ModalView
from kivy.properties import DictProperty, ObjectProperty, BooleanProperty
from config import keys as config_keys
from functools import partial


class AutosizeModal(ModalView):
    force_pos = DictProperty()
    widget = ObjectProperty()
    animation = BooleanProperty(False)
    input_focus = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(AutosizeModal, self).__init__(**kwargs)
        w = self.widget
        # self.prev_down_stamp = None
        self.add_widget(w)
        if all(map(w.is_event_type, ('on_input_focus', 'on_input_defocus'))):
            w.bind(on_input_focus=self._handle_input_focus)
        if w.is_event_type('on_close'):
            w.bind(on_close=partial(self.dismiss, animation=self.animation, force=True))
        if w.size_hint_x:
            self.size_hint_x = w.size_hint_x
            w.size_hint_x = 1
        else:
            self.size_hint_x = None
            self.width = w.width
            w.bind(width=self.setter('width'))
        if w.size_hint_y:
            self.size_hint_y = w.size_hint_y
            w.size_hint_y = 1
        else:
            self.size_hint_y = None
            self.height = w.height
            w.bind(height=self.setter('height'))

    def _handle_input_focus(self, widget, focus):
        self.input_focus = focus

    def on_key_down(self, instance, key, keycode, *largs):
        if key == config_keys['back']:
            if self.input_focus:
                self.widget.dispatch('on_input_defocus')
            else:
                self.dismiss(animation=self.animation)
            return True

    def _align_center(self, *l):
        pass

    def _update_center(self, *args):
        if not self.force_pos:
            return super(AutosizeModal, self)._update_center(args)
        for k, v in self.force_pos.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)

    def _real_remove_widget(self):
        if self._window:
            self._window.unbind(on_key_down=self.on_key_down)
        super(AutosizeModal, self)._real_remove_widget()

    def open(self, *largs):
        #super(AutosizeModal, self).open()
        if self._window is not None:
            return self
        # search window
        self._window = self._search_window()
        if not self._window:
            return self
        self._window.add_widget(self)
        self._window.bind(
            on_resize=self._align_center,
            on_keyboard=self._handle_keyboard)
        self.center = self._window.center
        self.bind(size=self._update_center)

        if self.animation:
            from kivy.animation import Animation
            a = Animation(_anim_alpha=1., d=self._anim_duration)
            a.bind(on_complete=lambda *x: self.dispatch('on_open'))
            a.start(self)

        # new stuff
        if self._window:
            self._window.bind(on_key_down=self.on_key_down)
        self._update_center()

        # call on open
        if not self.animation:
            self.on_open()

    def dismiss(self, *largs, **kwargs):
        if hasattr(self.widget, 'allow_dismiss') and not self.widget.allow_dismiss:
            return False
        kwargs['animation'] = self.animation
        super(AutosizeModal, self).dismiss(*largs, **kwargs)

    def on_dismiss(self):
        if self.widget.is_event_type('on_dismiss'):
            self.widget.dispatch('on_dismiss')

    # # add double tap to dismiss
    # def on_touch_down(self, touch):
    #     if not self.collide_point(*touch.pos):
    #         if self.auto_dismiss:
    #             if self.dismiss():
    #                 return True
    #
    #         from kivy.clock import Clock
    #         if not self.prev_down_stamp:
    #             self.prev_down_stamp = Clock.get_time()
    #         elif Clock.get_time()-self.prev_down_stamp < 1.0:
    #             print 'Double tap -- removing modal view'
    #             super(AutosizeModal, self).dismiss(force=True)
    #             return True
    #
    #     super(ModalView, self).on_touch_down(touch)
    #     return True
    #
    # def on_touch_move(self, touch):
    #     self.prev_down_stamp = None
    #     super(ModalView, self).on_touch_move(touch)
    #     return True
