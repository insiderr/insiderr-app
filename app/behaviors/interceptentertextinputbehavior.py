from kivy.properties import BooleanProperty


class InterceptEnterTextInputBehavior(object):
    ''' A custom behavior class that allows terminating input on 'enter' even when in multiline mode.
        This is helpful since a text input widget doesn't support text wrapping on multiline=False mode
        which is a shame :)
    '''
    intercept_enter_in_multiline = BooleanProperty(True)

    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        return super(InterceptEnterTextInputBehavior, self)._keyboard_on_key_down(window, keycode, text, modifiers)

    def _key_down(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale = key
        if self.multiline and self.intercept_enter_in_multiline and internal_action == 'enter':
            self.dispatch('on_text_validate')
            self.focus = False
        else:
            return super(InterceptEnterTextInputBehavior, self)._key_down(key, repeat)