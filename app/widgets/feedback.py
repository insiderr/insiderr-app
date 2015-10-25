from .layoutint import GridLayoutInt
from .biditextinput import BidiTextInput
from .autosizemodal import AutosizeModal
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import ObjectProperty
from api.feedbacks import post as post_feedback


class FeedbackTextInput(BidiTextInput):
    pass


class FeedbackButton(ButtonBehavior, GridLayoutInt):
    pass


class FeedbackDialog(GridLayoutInt):
    __events__ = ('on_dismiss', 'on_submit', 'on_close', 'on_input_focus', 'on_input_defocus')

    textinput = ObjectProperty()

    @staticmethod
    def open(**kwargs):
        AutosizeModal(widget=FeedbackDialog(),**kwargs).open()

    def on_dismiss(self):
        self.textinput.focus = False

    def on_submit(self):
        text = self.textinput.text.strip()
        if text:
            from modules.core.android_utils import Toast
            Toast('feedback sent')
            post_feedback(content=text)
        self.dispatch('on_close')

    def on_close(self):
        pass

    def on_input_focus(self, focus):
        pass

    def on_input_defocus(self):
        self.textinput.focus = False