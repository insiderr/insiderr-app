import kivy
kivy.require('1.8.0')

from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock


class InteractiveScreen(Screen):
    __events__ = ('on_back',)

    enter_trnasition = None
    leave_transition = None
    exit_on_close = BooleanProperty(False)

    prev_back_timestamp = 0

    entered_from = None

    def handle_app_stop(self):
        pass

    def handle_app_pause(self):
        pass

    def on_back(self, isdoubleback):
        pass

    def on_pre_enter(self, *args):
        m = self.manager
        if m and m.last_screen:
            self.entered_from = m.last_screen

    def trigger_back(self):
        isdoubleback = True
        actually_prev_timestamp = self.prev_back_timestamp
        self.prev_back_timestamp = Clock.get_time()
        if self.prev_back_timestamp - actually_prev_timestamp > 1 :
            isdoubleback = False

        self.dispatch('on_back', isdoubleback)
