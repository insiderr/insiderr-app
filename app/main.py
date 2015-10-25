# build version for android
__version__ = '0.102'

# make sure we do not store log into a file, there is no reason to.
from os import environ
environ['KIVY_NO_FILELOG'] = '1'

from kivy import require
require('1.8.0')

from kivy.config import Config
Config.set('graphics', 'maxfps', 90)
Config.set('graphics', 'vsync', 0)

from kivy import platform
print 'Running on %s' % platform
if platform in ['win', 'windows', 'linux', 'macosx']:
    Config.set('graphics', 'position', 'custom')
    Config.set('graphics', 'top', '20')
    Config.set('graphics', 'resizable', 0)
    if platform in ['linux', 'macosx']:
        Config.set('graphics', 'left', '2000')
        Config.set('graphics', 'width', '540')
        Config.set('graphics', 'height', '960')
    else:
        Config.set('graphics', 'left', '20')
        Config.set('graphics', 'width', '540')
        Config.set('graphics', 'height', '960')
elif platform in ['ios']:
    from os import getcwd
    cwd = getcwd() + '/basemodules'
    print 'python path: %s' % cwd
    import sys
    sys.path = [ cwd ] + sys.path

# Load opencv image support before everything!
from modules.image.img_opencv import ALoaderOpenCV
from kivy.core.image import ImageLoader

# might be smoother UI experience...
ALoaderOpenCV.max_upload_per_frame = 1
ALoaderOpenCV.num_workers = 1
ImageLoader.max_upload_per_frame = 1
ImageLoader.num_workers = 1

from config import set_app_version
set_app_version(__version__)

# Twisted initialization
from kivy.support import install_twisted_reactor
try:
    if platform in ['win', 'windows']:
        import sys 
        if 'twisted.internet.reactor' in sys.modules: 
            del sys.modules['twisted.internet.reactor']
    install_twisted_reactor()
except Exception as e:
    print('TWISTED: error installing -- %s' % str(e))

from kivy.app import App
from kivy.logger import Logger

# set refresh icon
ALoaderOpenCV.loading_image = ImageLoader.load('data/placeholder.png', allow_stretch=False)
ImageLoader.loading_image = ImageLoader.load('data/placeholder.png', allow_stretch=False)

# start login process in parallel to App initialization
from authentication import authenticate
def on_login(token):
    print ('on_start: logged in')
    from api.streams.posts import Manager as PostsManager
    PostsManager.logged_in = True
    from modules.core.android_utils import LogTestFairy
    LogTestFairy('Successful login ')

authenticate(on_login=on_login)

from kivy.factory import Factory
Factory.register('MainScreenManager', module='widgets.mainscreenmanager')
Factory.register('PostScreen', module='screens.post')
Factory.register('FeedScreen', module='screens.feed')
Factory.register('FavsScreen', module='screens.favs')
#Factory.register('WelcomeScreen', module='screens.welcome')
Factory.register('CommentsScreen', module='screens.comments')
Factory.register('Bar', module='widgets.bar')
Factory.register('ItemContainer', module='widgets.itemcontainer')
Factory.register('PostsContainer', module='screens.feed')
Factory.register('CommentsContainer', module='screens.comments')
Factory.register('UserPostTemplate', module='widgets.post')
Factory.register('ImageButton', module='widgets.imagebutton')
Factory.register('ImageToggleButton', module='widgets.imagebutton')
Factory.register('FavsContainer', module='screens.favs')

# might be smoother UI experience... default is 20
from kivy.clock import Clock
Clock.max_iteration = 10

# Make sure our window is initially transparent
#from kivy.core.window import Window
#Window.clearcolor = (0, 0, 0, 0)

# CRC init - not needed
#from modules.core.crc64 import CRC64
#CRC64("CRC64initalization")

from behaviors.keymanagerbehavior import KeyManagerBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
#from screens.welcome import WelcomeScreen
from screens.feed import FeedScreen
from screens.post import PostScreen
from focusmanager import FocusManager
#from kivy.clock import Clock


class Root(FloatLayout):
    manager = ObjectProperty()

    def on_manager(self, *largs):
        postscreen = None
        def on_comelete_reg(*largs):
            # update fields in post screen
            if postscreen:
                postscreen.update_role_desc_linkedin()

            # store the login keys only when we complete the linkedin authentication
            from utilities.auth_store import store_keys
            store_keys()

        #if not user_authenticated_on_session_start:
        #    self.manager.add_widget(WelcomeScreen(on_complete=on_comelete_reg))
        fs = FeedScreen()
        fs.bind(on_back=self.on_feed_screen_back)
        self.manager.add_widget(fs)

        # Pre-load the post screen to avoid first-time entry delay
        postscreen = PostScreen()
        self.manager.add_widget(postscreen)

    def on_feed_screen_back(self, screen, isdoubleback):
        if isdoubleback:
            self.exit_app()
            return True
        return False

    def exit_app(self):
        if platform == 'android':
            # go to home
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            theActivity = PythonActivity.mActivity
            # Switch to home screen to force our App to pause
            homeIntent = Intent(Intent.ACTION_MAIN)
            homeIntent.addCategory(Intent.CATEGORY_HOME)
            homeIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            theActivity.startActivity(homeIntent)
        else:
            # Exit explicitly
            from kivy.base import stopTouchApp
            stopTouchApp()

    def handle_app_pause(self):
        if self.manager.current_screen:
            self.manager.current_screen.handle_app_pause()

    def handle_app_stop(self):
        if self.manager.current_screen:
            self.manager.current_screen.handle_app_stop()


class InsiderrApp(KeyManagerBehavior, App):
    def __init__(self, **kwargs):
        super(InsiderrApp, self).__init__(**kwargs)

    def on_stop(self):
        # signal all async worker to shutdown
        from utilities.notification import startNotificationService
        startNotificationService()
        from utilities.threads import async_gloabl_threads_destrcution
        async_gloabl_threads_destrcution()
        FocusManager.defocus_all()
        self.root.handle_app_stop()
        return True

    def build(self):
        if platform in ['win', 'windows']:
            import sys
            if len(sys.argv)>1:
                self.title = 'Insiderr %s' % sys.argv[1]
        return Root()

    def on_start(self):
        # on ios we have to change the status bar color right when we are up.
        if platform == 'ios':
            from pyobjus import autoclass, objc_str
            ObjcClass = autoclass('ObjcClassINSD')
            o_instance = ObjcClass.alloc().init()
            o_instance.lightStatusBar()
        print('App started')
        from modules.core.android_utils import RemoveTutorialScreen
        RemoveTutorialScreen()
        from modules.core.android_utils import Toast
        Toast('logging in...', True)
        from utilities.notification import stopNotificationService, getLastNotificationMessage
        stopNotificationService()
        # make sure that if we started from a notification we act accordingly.
        keys = getLastNotificationMessage()
        if keys:
            from kivy.clock import Clock
            def switchscreens(*largs):
                from api.streams.posts import Manager as PostsManager
                if not PostsManager.logged_in:
                    Clock.schedule_once(switchscreens, 0.125)
                    return
                if len(keys) == 1:
                    s = self.root.manager.get_screen('favs')
                    s.fake_click_for_item = keys[0]
                self.root.manager.current = 'favs'
            Clock.schedule_once(switchscreens, 0.125)

    def open_settings(self, *largs):
        ''' Prevent the settings panel from appearing '''
        pass

    def on_pause(self):
        from utilities.notification import startNotificationService
        startNotificationService()
        FocusManager.defocus_all()
        # maybe store/sync a few things before...
        self.root.handle_app_pause()
        return True

    def on_resume(self):
        from utilities.notification import stopNotificationService, getLastNotificationMessage
        stopNotificationService()
        keys = getLastNotificationMessage()
        if keys:
            if len(keys) == 1:
                s = self.root.manager.get_screen('favs')
                s.fake_click_for_item = keys[0]
            self.root.manager.current = 'favs'

        print 'Notification Keys: %s' % str(keys)


if __name__ in ('__main__',):
    try:
        InsiderrApp().run()
    except Exception as e:
        from kivy.logger import Logger
        import traceback
        tb = traceback.format_exc()
        Logger.info('MAIN ERROR: %s' % tb)
