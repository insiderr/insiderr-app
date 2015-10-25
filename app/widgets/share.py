from .layoutint import GridLayoutInt
from .autosizemodal import AutosizeModal
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, ObjectProperty
from kivy.logger import Logger
from config import share_actions
from kivy import platform


SHARE_LINK = 'Check out Insiderr Your Anonymous Business Network http://insiderr.com'


class ShareItem(ButtonBehavior, GridLayoutInt):
    title = StringProperty()
    key = StringProperty()

    def __init__(self, **kwargs):
        super(ShareItem, self).__init__(**kwargs)


class ShareDialog(GridLayoutInt):
    __events__ = ('on_close',)
    item = ObjectProperty()
    share_providers = None

    def __init__(self, **kwargs):
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Share post popup')
        #LogTestFairy('Share post popup screen')
        super(ShareDialog, self).__init__(**kwargs)
        self.populate()

    @staticmethod
    def open(item):
        widget = ShareDialog(item=item)
        AutosizeModal(widget=widget).open()

    def on_close(self):
        pass

    def get_key_in_providers(self, key):
        ALWAYS = 'ALWAYS'
        if platform == 'android':
            share_to_providers = {
                'linkedin': 'linkedin',
                'facebook': 'facebook',
                'twitter': 'twitter',
                'message': 'mms',
                'whatsapp': 'whatsapp',
                'more-options': ALWAYS,
            }
        else:
            share_to_providers = {
                'more-options': ALWAYS,
            }

        providers = self.get_available_share_providers()
        provider_key = share_to_providers.get(key, None)
        if not provider_key:
            return None
        if provider_key is ALWAYS:
            # empty not not None
            return ''
        for p in providers:
            if provider_key in p.lower():
                return p
        return None

    def populate(self):
        for action in share_actions:
            # skip the active test - just test on click
            #active = self.get_key_in_providers(action['key']) is not None
            #print 'action %s is %s' % (action ,active)
            #si = ShareItem(active=active, **action)
            si = ShareItem(active=True, **action)
            si.bind(on_release=self.share_clicked)
            self.add_widget(si)

    def get_available_share_providers(self):
        if self.share_providers:
            return self.share_providers

        from kivy import platform
        if platform == 'android':
            from jnius import autoclass, cast
            Intent = autoclass('android.content.Intent')
            shareIntent = Intent(Intent.ACTION_SEND)
            shareIntent.setType("image/jpeg")
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            context = cast('android.content.Context', PythonActivity.mActivity)
            resInfo = context.getPackageManager().queryIntentActivities(shareIntent, 0)
            from modules.core.android_utils import map_List
            self.share_providers = map_List(
                    lambda x: str(x.activityInfo.packageName),
                    resInfo)

            print 'SHARING PROVIDERS -- %s' % self.share_providers
            return self.share_providers
        else:
            self.share_providers = ['']
            return self.share_providers

    def share_clicked(self, touch):
        from modules.core.android_utils import LogTestFairy
        action = touch.key
        Logger.info('ShareDialog: %s clicked' % action)
        LogTestFairy('Share post on %s' % action)
        from modules.core.tempstorage import get_temp_folder_prefix
        fname = get_temp_folder_prefix() + 'share.jpg'
        Logger.info('ShareDialog: Storing image to %s' % fname)
        try:
            self.item.texture.save(fname)
        except:
            Logger.info('ShareDialog: failed Storing %s' % fname)
            self.dispatch('on_close')
            return

        # make sure everyone can access it
        Logger.info('ShareDialog: Done Storing %s' % fname)

        provider = self.get_key_in_providers(action)

        from kivy import platform
        if platform == 'ios':
            from pyobjus import autoclass, objc_str
            ObjcClass = autoclass('ShareViewControllerINDR')
            self.o_instance = ObjcClass.alloc().init()
            self.o_instance.aTitle = objc_str(SHARE_LINK)
            self.o_instance.aFileName = objc_str(fname)
            self.o_instance.aApp = objc_str(action)
            self.o_instance.aURL = objc_str('http://insiderr.com')
            self.o_instance.shareImagePost()

        elif platform == 'android':
            from jnius import autoclass, cast
            AndroidString = autoclass('java.lang.String')
            Uri = autoclass('android.net.Uri')
            # start android intent stuff
            File = autoclass('java.io.File')
            sharedFile = File(fname)
            phototUri = Uri.fromFile(sharedFile)
            Intent = autoclass('android.content.Intent')
            shareIntent = Intent(Intent.ACTION_SEND)
            shareIntent.setType("image/*")
            shareIntent.setFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            if provider:
                shareIntent.setPackage(provider)
            if 'facebook' in action:
                shareIntent.putExtra(Intent.EXTRA_TEXT, AndroidString("http://insiderr.com"))
            else:
                shareIntent.putExtra(Intent.EXTRA_TEXT, AndroidString(SHARE_LINK))
            shareIntent.putExtra("sms_body", AndroidString(SHARE_LINK))
            shareIntent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', phototUri))
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            theActivity = PythonActivity.mActivity
            chooser_title = cast('java.lang.CharSequence', AndroidString('Share Via'))
            theActivity.startActivity(Intent.createChooser(shareIntent, chooser_title))

        self.dispatch('on_close')
        LogTestFairy('Shared post successfully')
