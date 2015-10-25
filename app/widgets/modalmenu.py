from widgets.layoutint import GridLayoutInt
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.logger import Logger


class ModalMenuItem(ButtonBehavior, GridLayoutInt):
    title = StringProperty()
    action = StringProperty()

    def __init__(self, **kwargs):
        super(ModalMenuItem, self).__init__(**kwargs)


class ModalMenu(GridLayoutInt):
    __events__ = ('on_close',)
    border = NumericProperty(0)
    border_color = ListProperty([.5, .5, .5, 1])
    show_top_border = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(ModalMenu, self).__init__(**kwargs)

    def add_widget(self, widget, index=0):
        super(ModalMenu, self).add_widget(widget, index)
        if isinstance(widget, ButtonBehavior):
            widget.bind(on_release=self.button_clicked)

    def on_close(self):
        pass

    def button_clicked(self, item):
        self.dispatch('on_close')