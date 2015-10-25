from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from widgets.layoutint import GridLayoutInt
from kivy.uix.image import Image
from kivy.properties import StringProperty, ListProperty, ObjectProperty, NumericProperty, BooleanProperty
from kivy.compat import string_types
from kivy.factory import Factory


class BarMiddleLabel(Label):
    pass


class BarMiddleImage(Image):
    pass


class BarMiddleButton(ButtonBehavior, GridLayoutInt):
    title = StringProperty()


class Bar(GridLayoutInt):
    __events__ = ('on_left_click', 'on_right_click')

    screen = ObjectProperty()
    color = ListProperty([1, 1, 1, 1])
    left_icon = StringProperty('')
    right_icon = StringProperty('')
    hide_right_icon = BooleanProperty(False)
    middle_cls = ObjectProperty(None, allownone=True)
    middle = ObjectProperty()
    shadow_height = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Bar, self).__init__(**kwargs)
        self._resolve_middle_cls()
        self.bind(middle_cls=self._resolve_middle_cls)

    def _resolve_middle_cls(self, *args):
        if not self.middle_cls:
            return
        if self.middle:
            self.remove_widget(self.middle)
        middle_cls = self.middle_cls
        if isinstance(middle_cls, string_types):
            middle_cls = Factory.get(middle_cls)
        self.middle = middle_cls(screen=self.screen)
        self.add_widget(self.middle, 1)

    def on_left_click(self, button_box):
        pass

    def on_right_click(self, button_box):
        pass
