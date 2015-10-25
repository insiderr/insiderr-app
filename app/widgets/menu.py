from kivy.properties import StringProperty, NumericProperty, ListProperty
from widgets.layoutint import GridLayoutInt
from widgets.customdropdown import CustomDropDown
from kivy.uix.behaviors import ToggleButtonBehavior
from behaviors.togglebuttongroupbehavior import ToggleButtonGroupBehavior
from theme import _scale_to_theme_dpi

class MenuItemBase(ToggleButtonBehavior, GridLayoutInt):
    pass


class MenuItem(ToggleButtonGroupBehavior, MenuItemBase):
    title = StringProperty()
    font_name = StringProperty('fonts/Alef-Regular.ttf')
    font_size = NumericProperty(12)


class Menu(CustomDropDown):
    background_color = ListProperty([0, 0, 0, 1])
    outline_color = ListProperty([1., 1., 1., 1])
    item_sep_height = NumericProperty(_scale_to_theme_dpi(1))
    item_sep_margin = NumericProperty(_scale_to_theme_dpi(1))

    def __init__(self, **kwargs):
        super(Menu, self).__init__(**kwargs)
        self.bind(item_sep_height=self._set_item_sep_height)
        self._set_item_sep_height()

    def _set_item_sep_height(self):
        c = self.container
        if c:
            c.padding[1] += self.item_sep_height
            c.padding[3] += self.item_sep_height
            c.spacing[1] += self.item_sep_height

    def _item_state_changed(self, item, value):
        if value == 'down':
            self.select(item)

    def on_container(self, instance, value):
        super(CustomDropDown, self).on_container(instance, value)
        for w, largs in getattr(self, 'queued_items', []):
            self.add_widget(w, *largs)
        self.queued_items = []

    def add_widget(self, widget, *largs):
        if isinstance(widget, MenuItem):
            widget.bind(state=self._item_state_changed)
            widget.item_sep_margin = self.item_sep_margin
            if not self.container:
                self.queued_items = getattr(self, 'queued_items', []) + [(widget, largs)]
                return
        super(Menu, self).add_widget(widget, *largs)
        self.scroll_y = 0
        self.scroll_x = 0

    def open(self, widget, selected=None):
        if selected:
            for i in self.items():
                if i.title == selected:
                    i.state = 'down'
                    break
        else:
            for i in self.items():
                i.state = 'normal'
        super(Menu, self).open(widget)