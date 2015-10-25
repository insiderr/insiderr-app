from kivy.utils import platform
from kivy.logger import Logger
from network.google_analytics import post as post_ga


def StartNotificationsService(headers, url, keys, systemurl):
    # start notification service
    Logger.info('StartNotificationsService:\nURL=%s\nKeys=%s' % (url, keys))

    if platform == 'android':
        try:
            AUTH = headers.get('Authorization', '')[0]
            from api import add_params
            KEYS = add_params('', allow_multiple=True, key=keys, kind='Comment')
            print('starting notification service')
            from jnius import autoclass
            String = autoclass('java.lang.String')
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            theActivity = PythonActivity.mActivity
            aURL = String(url)
            aAUTH = String(AUTH)
            aKEYS = String(KEYS)
            aSYSTEMURL = String(systemurl)
            theActivity.startService(aURL, aAUTH, aKEYS, aSYSTEMURL)
        except:
            print('starting notification service -- failed')
            pass


def StopNotificationsService():
    # disable notification service
    if platform == 'android':
        # from android.runnable import run_on_ui_thread
        try:
            print('stopping notification service')
            from jnius import autoclass
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            theActivity = PythonActivity.mActivity
            theActivity.stopService()
        except:
            print('stopping notification service -- failed')
            pass


def GetLastNotificationMessage():
    lastNotificationMessage = ''
    if platform == 'android':
        # go to home
        from jnius import autoclass
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        theActivity = PythonActivity.mActivity
        lastNotificationMessage = theActivity.getLastNotificationMessage()

    return lastNotificationMessage


def RemoveTutorialScreen():
    if platform == 'android':
        from android.runnable import run_on_ui_thread
        @run_on_ui_thread
        def ui_RemoveTutorialScreen():
            try:
                print('removing tutorial screen')
                from jnius import autoclass
                PythonActivity = autoclass('org.renpy.android.PythonActivity')
                theActivity = PythonActivity.mActivity
                theActivity.removeTutotrial()
            except:
                print('removing tutorial screen -- failed')
                pass

        ui_RemoveTutorialScreen()

ToastObject = None
def Toast(text, length_long=False):
    if platform == 'android':
        from android.runnable import run_on_ui_thread
        @run_on_ui_thread
        def ui_toaster(text, length_long=False):
            from jnius import autoclass, cast
            global ToastObject
            if not ToastObject:
                ToastObject = autoclass('android.widget.Toast')
            context = autoclass('org.renpy.android.PythonActivity').mActivity
            duration = ToastObject.LENGTH_LONG if length_long else ToastObject.LENGTH_SHORT
            String = autoclass('java.lang.String')
            c = cast('java.lang.CharSequence', String(text))
            t = ToastObject.makeText(context, c, duration)
            t.show()

        ui_toaster(text, length_long)
    elif platform == 'ios':
        global ToastObject
        from pyobjus import autoclass, objc_str
        if not ToastObject:
            oToasObject = autoclass('ToastINSD')
            ToastObject = oToasObject.alloc().init()
        ToastObject.aText = objc_str(text)
        ToastObject.showToastBar()

    else:
        print 'TOAST: %s' % text


def ShareActivity(text, title=None):
    if not title:
        title = 'Share Via'
    if platform == 'android':
        try:
            from jnius import autoclass, cast
            AndroidString = autoclass('java.lang.String')
            Uri = autoclass('android.net.Uri')
            # start android intent stuff
            Intent = autoclass('android.content.Intent')
            shareIntent = Intent(Intent.ACTION_SEND)
            shareIntent.setType("text/plain")
            shareIntent.putExtra(Intent.EXTRA_TEXT, AndroidString(text))
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            theActivity = PythonActivity.mActivity
            chooser_title = cast('java.lang.CharSequence', AndroidString(title))
            theActivity.startActivity(Intent.createChooser(shareIntent, chooser_title))
        except:
            print 'Failed sharing text -- %s' % text
            pass
    elif platform == 'ios':
        from pyobjus import autoclass, objc_str
        ObjcClass = autoclass('ShareViewControllerINDR')
        o_instance = ObjcClass.alloc().init()
        if not title:
            title = ''
        o_instance.aTitle = objc_str(title)
        o_instance.aApp = objc_str('link')
        o_instance.aURL = objc_str(text)
        o_instance.shareImagePost()
    else:
        print 'Sharing: %s -- %s' % (title, text)


def OpenUrlActivity(url):
    if url.find("https://") != 0 and url.find("http://") != 0:
        url = "http://"+url

    if platform == 'android':
        try:
            from jnius import autoclass, cast
            Uri = autoclass('android.net.Uri')
            Intent = autoclass('android.content.Intent')
            viewIntent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            theActivity = PythonActivity.mActivity
            theActivity.startActivity(viewIntent)
        except:
            print 'Failed opening url %s' % url
            pass
    else:
        import webbrowser
        webbrowser.open(url, new=1, autoraise=True)


_androidLogger = None
_androidLoggerPrevTS = None
def LogTestFairy(text):
    if platform == 'android':
        global _androidLogger
        if not _androidLogger:
            from jnius import autoclass
            _androidLogger = autoclass('android.util.Log')
        _androidLogger.v("testfairy-checkpoint", text)
        # print to log
        print 'testfairy-checkpoint: %s' % (text)
    else:
        # print timestamp to log
        global _androidLoggerPrevTS
        from datetime import datetime
        if not _androidLoggerPrevTS:
            _androidLoggerPrevTS = datetime.now()
        timediff = datetime.now() - _androidLoggerPrevTS
        print 'testfairy-checkpoint: %sms : %s' % (timediff.total_seconds() * 1000.0, text)
    # put into google analytics
    post_ga(text)


def BuildVERSION():
    if platform == 'android':
        from jnius import autoclass
        BuildVERSION = autoclass('android.os.Build$VERSION')
        sdk_version = int(BuildVERSION.SDK_INT)
        return BuildVERSION, sdk_version

def string_to_CharSequence(s):
    if platform == 'android':
        from jnius import cast, autoclass
        String = autoclass('java.lang.String')
        return cast('java.lang.CharSequence', String(s))

def map_List(func, l):
    res = []
    if l is not None:
        it = l.iterator()
        while it.hasNext():
            res.append(func(it.next()))
    return res

