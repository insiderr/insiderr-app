from kivy.logger import Logger
from kivy.properties import BooleanProperty
from behaviors.boundedtextinputbehavior import BoundedTextInputBehavior
from widgets.biditextinput import BidiTextInput


class WrappableTextInput(BoundedTextInputBehavior, BidiTextInput):
    ''' A custom text input class that allows terminating input on 'enter' even when in multiline mode.
        This is helpful since a text input widget doesn't support text wrapping on multiline=False mode
        which is a shame :)
    '''
    intercept_enter_in_multiline = BooleanProperty(True)

    def on_touch_down(self, touch):
        miny = self.height
        maxy = 0
        T = 0

        if self.text or ( self._lines_rects and len(self._lines_rects)>0 and
                                  not self._lines_rects[0].needs_redraw and self._lines_rects[0].size[1]>0 ):
            line_rects = self._lines_rects
        else:
            line_rects = self._hint_text_rects

        for c in line_rects:
            # if c.needs_redraw:
            #     continue
            miny = min(miny,c.pos[1])
            maxy = max(maxy,c.pos[1]+c.size[1])
            T = max(T,c.size[1])

        if T>0 and ( touch.y < miny-T or touch.y > maxy+T ):
            self.focus = False
            return

        super(WrappableTextInput, self).on_touch_down(touch)

    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        return super(WrappableTextInput, self)._keyboard_on_key_down(window, keycode, text, modifiers)

    def _key_down(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale = key
        if self.multiline and self.intercept_enter_in_multiline and internal_action == 'enter':
            self.dispatch('on_text_validate')
            self.focus = False
        else:
            return super(WrappableTextInput, self)._key_down(key, repeat)
