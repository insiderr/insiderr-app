


class FocusManagerImpl(object):
    focused_elements = set()

    def on_focus(self, element, focused):
        if focused:
            self.focused_elements.add(element)
        else:
            self.focused_elements.remove(element)

    def defocus_all(self):
        elements = self.focused_elements.copy()
        for e in elements:
            e.focus = False


FocusManager = FocusManagerImpl()