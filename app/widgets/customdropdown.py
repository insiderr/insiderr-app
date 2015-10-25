from kivy.uix.dropdown import DropDown
from kivy.properties import NumericProperty, BooleanProperty


class CustomDropDown(DropDown):
    place_center = BooleanProperty(True)
    place_size_hint_x = NumericProperty(None, allownone=True)

    def items(self):
        return self.container.children

    def _reposition(self, *largs):
        # calculate the coordinate of the attached widget in the window
        # coordinate system
        win = self._win
        widget = self.attach_to
        if not widget or not win:
            return
        wx, wy = widget.to_window(*widget.pos)
        wright, wtop = widget.to_window(widget.right, widget.top)

        # set width and x
        if self.auto_width:
            if self.place_size_hint_x:
                self.width = (wright - wx) * self.place_size_hint_x
            else:
                self.width = (wright - wx)

        if self.place_center:
            cx, cy = widget.to_window(*widget.center)
            x = cx - self.width / 2
        else:
            x = wx

        # ensure the dropdown list doesn't get out on the X axis, with a
        # preference to 0 in case the list is too wide.
        if x + self.width > win.width:
            x = win.width - self.width
        if x < 0:
            x = 0
        self.x = x

        # determine if we display the dropdown upper or lower to the widget
        h_bottom = wy - self.height
        h_top = win.height - (wtop + self.height)
        if h_bottom > 0:
            self.top = wy
        elif h_top > 0:
            self.y = wtop
        else:
            # none of both top/bottom have enough place to display the
            # widget at the current size. Take the best side, and fit to
            # it.
            height = max(h_bottom, h_top)
            if height == h_bottom:
                self.top = wy
                self.height = wy
            else:
                self.y = wtop
                self.height = win.height - wtop