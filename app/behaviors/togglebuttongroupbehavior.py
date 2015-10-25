from kivy.uix.behaviors import ToggleButtonBehavior


class ToggleButtonGroupBehavior(ToggleButtonBehavior):
    def _do_press(self):
        ''' Don't allow state to be changed from 'down' to 'normal' using press
            In such a case just re-assert the existing state.
        '''
        self._release_group(self)
        if self.state == 'down':
            self.property('state').dispatch(self)
        else:
            self.state = 'down'