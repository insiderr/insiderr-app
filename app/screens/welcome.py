from kivy.logger import Logger
from screens import InteractiveScreen
from config import tutorial_path
from kivy.properties import ObjectProperty, OptionProperty, BooleanProperty, StringProperty, NumericProperty
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from os import listdir
from os.path import join
from authentication import user_authenticated
from widgets.linkedin import LinkedIn
from kivy.utils import platform
from theme import anonymous_nick


class TutorialImage(FloatLayout):
    source = StringProperty()


class TutorialProgressImage(Image):
    status = OptionProperty('dark', options=('dark', 'light'))


class TutorialSkipButton(ButtonBehavior, Label):
    hide = BooleanProperty(False)

class HiddenButton(ButtonBehavior, Label):
    __events__ = ('on_hidden_press',)
    hold_threshold = NumericProperty(10.)

    def on_hidden_press(self):
        pass

    def on_touch_down(self, touch):
        if super(HiddenButton, self).on_touch_down(touch):
            from time import time
            self.ts = time()

    def on_touch_up(self, touch):
        if super(HiddenButton, self).on_touch_up(touch):
            if platform is not 'android' and touch.is_double_tap:
                self.dispatch('on_hidden_press')
            else:
                from time import time
                self.ts = time()-self.ts
                if self.ts > self.hold_threshold:
                    self.dispatch('on_hidden_press')


class WelcomeScreen(InteractiveScreen):
    __events__ = ('on_complete',)

    carousel = ObjectProperty()
    progress_indicator = ObjectProperty()
    skip_button = ObjectProperty()

    def set_index(self, index):
        if self.progress_indicator:
            pis = list(reversed(self.progress_indicator.children))
            for c in pis[:index + 1]:
                c.status = 'dark'
            for c in pis[index + 1:]:
                c.status = 'light'
            self.update_skip_button(index=index)

    def update_skip_button(self, index=None):
        index = index or self.carousel.index
        self.skip_button.hide = (index == len(self.carousel.slides) - 1)
        if self.skip_button.hide:
            from modules.core.android_utils import LogTestFairy
            LogTestFairy('Login Screen')

    def _linkedin_login_completed(self, *largs):
        user_profile = largs[1] if len(largs) >1 else None
        if user_profile:
            from config import linkedin_ds
            industry = user_profile.get('industry','unknown')
            expertise = 'unknown'
            if user_profile.get('skills',None):
                try:
                    skills = user_profile.get('skills').get('values', None)
                    expertise = skills[0]['skill']['name']
                except:
                    print 'Error parsing linkedin skills -- %s' % user_profile

            company = 'unknown'
            position = 'unknown'
            if user_profile.get('threeCurrentPositions',None):
                try:
                    positions = user_profile.get('threeCurrentPositions').get('values', None)
                    company = positions[0]['company']['name']
                    position = positions[0]['title']
                except:
                    print 'Error parsing linkedin company/position -- %s' % user_profile

            def update(ds):
                ds.update({
                    'anonymous': anonymous_nick,
                    'industry': industry,
                    'company': company,
                    'position': position,
                    'expertise': expertise
                })
            linkedin_ds.update(update)
        self.dispatch('on_complete')

    def on_pre_enter(self):
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Tutorial')
        if self.carousel:
            self.populate()
        else:
            self.bind(
                carousel=self._populate_when_ready,
                progress_indicator=self._populate_when_ready)

    def _populate_when_ready(self, *largs):
        if self.carousel and self.progress_indicator:
            self.populate()

    def populate(self):
        if not self.carousel.slides:
            self.populate_slides()
            self.populate_progress()

    def populate_slides(self):
        for file in sorted(listdir(tutorial_path)):
            self.carousel.add_widget(
                TutorialImage(
                    source=join(tutorial_path, file)))
        if not user_authenticated():
            linkedin = LinkedIn()
            linkedin.bind(on_complete=self._linkedin_login_completed)
            self.carousel.add_widget(linkedin)
        self.update_skip_button()

    def populate_progress(self):
        first = True
        for c in self.carousel.slides:
            self.progress_indicator.add_widget(
                TutorialProgressImage(status='dark' if first else 'light'))
            first = False

    def on_leave(self, *args):
        # Note: a bug in kivy will cause this to throw an index exception
        if self.carousel:
            self.carousel.clear_widgets()

    def skip_to_last(self):
        try:
            self.carousel.load_slide(self.carousel.slides[-1])
            self.set_index(len(self.carousel.slides) - 1)
        except Exception as ex:
            pass

    def on_complete(self):
        # store the login keys only when we complete the linkedin authentication
        from utilities.auth_store import store_keys
        store_keys()
