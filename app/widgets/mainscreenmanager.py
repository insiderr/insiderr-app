from kivy.uix.screenmanager import ScreenManager


class MainScreenManager(ScreenManager):
    last_screen = None

    def _resolve_transition(self, name):
        if self.has_screen(name):
            ns = self.get_screen(name)
            cs = self.current_screen
            if ns and getattr(ns, 'enter_t', None):
                return ns.enter_t
            elif cs and getattr(cs, 'leave_t', None):
                return cs.leave_t

    def _resolve_screen(self, name):
        if name == 'favs':
            from screens.favs import FavsScreen
            return FavsScreen()
        elif name == 'post':
            from screens.post import PostScreen
            return PostScreen()
        elif name == 'comments':
            from screens.comments import CommentsScreen
            return CommentsScreen()
        elif name == 'linkedin':
            from screens.linkedin import LinkedinScreen
            return LinkedinScreen()

    def get_screen(self, name):
        if name in self.screen_names:
            return super(MainScreenManager, self).get_screen(name)

        screen = self._resolve_screen(name)
        if screen:
            self.add_widget(screen)
        return screen

    def on_current(self, instance, value):
        if not self.has_screen(value):
            screen = self._resolve_screen(value)
            if not screen:
                return
            self.add_widget(screen)

        transition = self._resolve_transition(value)

        # taken from the base class
        screen = self.get_screen(value)
        if not screen:
            return
        if screen == self.current_screen:
            return

        self.transition.stop()

        if transition:
            self.transition = transition

        previous_screen = self.current_screen
        self.current_screen = screen
        if previous_screen:
            self.transition.screen_in = screen
            self.transition.screen_out = previous_screen
            self.transition.start(self)
        else:
            screen.pos = self.pos
            self.real_add_widget(screen)
            screen.dispatch('on_pre_enter')
            screen.dispatch('on_enter')
        # end: taken from the base class

        self.last_screen = value
