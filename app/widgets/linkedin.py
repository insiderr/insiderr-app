from kivy.logger import Logger
import BaseHTTPServer
from kivy import platform
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.event import EventDispatcher
from widgets.layoutint import GridLayoutInt
from config import linkedin_ds, post_roles
from kivy.uix.widget import Widget
from theme import anonymous_nick


class ClientRedirectServer(BaseHTTPServer.HTTPServer):
    """A server to handle OAuth 2.0 redirects back to localhost.

    Waits for a single request and parses the query parameters
    into query_params and then stops serving.
    """
    query_params = {}


class ClientRedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """A handler for OAuth 2.0 redirects back to localhost.

    Waits for a single request and parses the query parameters
    into the servers query_params and then stops serving.
    """
    def do_GET(s):
        try:
            from urlparse import parse_qsl
        except ImportError:
            from cgi import parse_qsl

        """Handle a GET request.

        Parses the query parameters and prints a message
        if the flow has completed. Note that we can't detect
        if an error occurred.
        """
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        query = s.path.split('?', 1)[-1]
        query = dict(parse_qsl(query))
        s.server.query_params = query
        s.wfile.write("<html><head><title>Authentication Status</title></head>")
        s.wfile.write("<body><p>Registration completed successfully</p><p>This window will be closed automatically in a few seconds.</p>")
        s.wfile.write("</body></html>")

    def log_message(self, format, *args):
        """Do not log messages to stdout while running as command line program."""
        pass


from kivy.clock import Clock

if platform in ['ios']:
    class Wv:
        def __init__(self, **kwargs):
            self._url = kwargs.get('url', 'http://www.google.com')
            self._localserve = kwargs.get('localserve', None)
            Clock.schedule_once(self.create_webview, 0)

        def create_webview(self, *args):
            from pyobjus import autoclass, objc_str
            ObjcClass = autoclass('ObjcClassINSD')
            self.o_instance = ObjcClass.alloc().init()
            self.o_instance.aParam1 = objc_str(self._url)
            self.o_instance.openWebView()
            self._localserve.dispatch('on_webview')

        def remove(self):
            self.o_instance.closeWebView()
            self._localserve.dispatch('on_webview_removed')

elif platform in ['android']:
    from android.runnable import run_on_ui_thread
    class Wv(Widget):

        def __init__(self, **kwargs):
            super(Wv, self).__init__(**kwargs)
            self._url = kwargs.get('url', 'http://www.google.com')
            self._localserve = kwargs.get('localserve', None)
            self._webview = None
            Clock.schedule_once(self.create_webview, 0)

        @run_on_ui_thread
        def create_webview(self, *args):
            from jnius import autoclass
            #VLayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
            LLayoutParams = autoclass('android.widget.LinearLayout$LayoutParams')
            #RLayoutParams = autoclass('android.widget.RelativeLayout$LayoutParams')
            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            activity = autoclass('org.renpy.android.PythonActivity').mActivity
            webview = WebView(activity)
            webview.getSettings().setJavaScriptEnabled(True)
            wvc = WebViewClient()
            webview.setWebViewClient(wvc)
            linear = LLayoutParams(-2, -2)
            linear.setMargins(100, 100, 100, 100)
            #relative = RLayoutParams(-2, -2)
            #relative.addRule(14, 1)
            #relative.addRule(15, 1)
            activity.addContentView(webview, linear)
            webview.loadUrl(self._url)
            self._webview = webview
            Logger.info('reschedule send on_webview')
            Clock.schedule_once(self.sendWebViewEvent, 1)

        def sendWebViewEvent(self, *args):
            Logger.info('sending on_webview')
            self._localserve.dispatch('on_webview')

        def remove(self, *args):
            Logger.info('schedule removing webview')
            if not self._webview:
                return
            Clock.schedule_once(self.remove_webview, 0)

        @run_on_ui_thread
        def remove_webview(self, *args):
            Logger.info('removing webview')
            from jnius import cast
            from jnius import autoclass
            webview = cast('android.widget.AbsoluteLayout', self._webview)
            webviewparent = webview.getParent()
            linearlayout = cast('android.widget.LinearLayout', webviewparent)
            linearlayout.removeView(webview)
            self._localserve.dispatch('on_webview_removed')
else:
    # desktops
    class Wv:
        def __init__(self, **kwargs):
            self._url = kwargs.get('url', 'http://www.google.com')
            self._localserve = kwargs.get('localserve', None)
            #self.create_webview()
            Clock.schedule_once(self.create_webview, 0)

        def create_webview(self, *args):
            import webbrowser
            webbrowser.open(self._url, new=1, autoraise=True)
            self._localserve.dispatch('on_webview')

        def remove(self):
            self._localserve.dispatch('on_webview_removed')


class LinkedIn(Widget):
    __events__ = ('on_complete', 'on_error', 'on_webview', 'on_webview_removed', 'on_request_served')

    consumer_token = None
    consumer_token_expiration = None
    linkedinapp = None
    in_webview = BooleanProperty(False)
    user_profile = None

    def __init__(self, **kwargs):
        super(LinkedIn, self).__init__(**kwargs)

    def getLinkedinToken(self):
        from modules.linkedin.linkedin import LinkedInAuthentication, LinkedInApplication, PERMISSIONS
        API_KEY = '##API_KEY##'
        API_SECRET = '##API_SECRET##'
        RETURN_HOST = 'localhost'
        RETURN_HOST_PORT = 8000
        RETURN_URL = 'http://'+RETURN_HOST+':'+str(RETURN_HOST_PORT)+'/'
        #APP_PERMISSIONS = (PERMISSIONS.FULL_PROFILE, )
        # no more full profile from linkedin - use basic
        APP_PERMISSIONS = (PERMISSIONS.BASIC_PROFILE, )
        self.authentication = LinkedInAuthentication(API_KEY, API_SECRET, RETURN_URL,
                                                APP_PERMISSIONS)
        authorize_url = self.authentication.authorization_url
        print self.authentication.authorization_url
        try:
            self.httpd = ClientRedirectServer((RETURN_HOST, RETURN_HOST_PORT),
                                         ClientRedirectHandler)
        except:
            return False

        Logger.info('Creating webview')
        self.webviewwidget = Wv(url=authorize_url, localserve=self)
        self.in_webview = True
        return True

    @staticmethod
    def _thread_handle_request(self, *largs):
        try:
            self.httpd.handle_request()
            self.webviewwidget.remove()
            self.query_params = self.httpd.query_params
            self.httpd.server_close()
            print 'request recieved'
        except:
            pass
        self.dispatch('on_request_served')
        if platform == "android":
            from jnius import autoclass
            try:
                Thread = autoclass('java.lang.Thread')
                Thread.currentThread().join()
            except:
                pass

    def on_webview(self):
        Logger.info('event on_webview')
        from thread import start_new_thread
        self.query_params = None
        start_new_thread(LinkedIn._thread_handle_request, (self,))
        print 'Waiting for request'

    def on_request_served(self):
        from modules.linkedin.linkedin import LinkedInApplication
        query_params = self.query_params
        code = None
        if 'error' in query_params:
            print 'Authentication request was rejected.'
            self.dispatch('on_error', 'Failed processing linkednin auth')
            return
        if 'code' in query_params:
            code = query_params['code']
        else:
            print 'Failed to find "code" in the query parameters of the redirect.'
            self.dispatch('on_error', 'Failed processing linkednin auth')
            return

        application = LinkedInApplication(self.authentication)
        self.authentication.authorization_code = code
        token = self.authentication.get_access_token()
        #print 'token=%s' % str(token.access_token)
        self.consumer_token = token.access_token
        self.consumer_token_expiration = token.expires_in
        self.linkedinapp = self.getLinkedinApp(token=self.consumer_token)
        try:
            #userProfile = self.linkedinapp.get_profile(selectors=['three-current-positions', 'location', 'distance', 'num-connections', 'skills', 'educations', 'industry'])
            #userProfile = self.linkedinapp.get_profile(selectors=['positions', 'location', 'num-connections', 'industry'])
            #userProfile = self.linkedinapp.get_profile(selectors=['positions', 'location', 'num-connections', 'industry', 'skills'])
            userProfile = self.linkedinapp.get_profile(selectors=['specialties', 'headline', 'positions', 'location', 'num-connections', 'industry', 'skills'])
            self.user_profile = userProfile
        except Exception as e:
            userProfile = ''
            print 'Failed to get profile: %s' % e

        #print 'linkedin PROFILE: %s' % str(userProfile)

        if self.process_user_profile(userProfile):
            self.dispatch('on_complete')
        else:
            self.dispatch('on_error', 'Failed processing user profile')

    def on_webview_removed(self):
        self.in_webview = False

    def getLinkedinApp(self, token=None):
        from modules.linkedin.linkedin import LinkedInApplication
        application = LinkedInApplication(token=token)
        return application

    def on_complete(self):
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Linkedin authentication succeeded')
        pass

    def on_error(self, reason):
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Linkedin authentication failed')

    def do_login(self):
        try:
            if not self.consumer_token:
                self.getLinkedinToken()

        except Exception as e:
            Logger.info('LinkenIn: exception -- %s' % str(e))
            import traceback
            tb = traceback.format_exc()
            Logger.info('LinkenIn stack: %s' % tb)
            self.dispatch('on_error', str(e))

    def process_user_profile(self, user_profile):
        if user_profile:
            industry = user_profile.get('industry','unknown')
            skills = []
            if user_profile.get('skills', None):
                try:
                    linkedin_skills = user_profile.get('skills').get('values', None)
                    for s in linkedin_skills:
                        skills.append( s['skill']['name'] )
                except:
                    print 'Error parsing linkedin skills -- %s' % user_profile

            if len(skills) < 1:
                skills = ['unknown']
            companies = []
            positions = []
            if user_profile.get('positions', None):
                try:
                    linkedin_positions = user_profile.get('positions').get('values', None)
                    for p in linkedin_positions:
                        ##if not p.get('endDate', None):
                        companies.append(p['company']['name'])
                        positions.append(p['title'])
                except:
                    print 'Error parsing linkedin company/position -- %s' % user_profile

            if len(companies) < 1:
                companies = ['unknown']
            if len(positions) < 1:
                positions = ['unknown']

            def update(ds):
                linkedin_profile = {
                    'anonymous': anonymous_nick,
                    'industry': industry,
                    'company': companies[0],
                    'company_options': companies,
                    'position': positions[0],
                    'position_options': positions,
                    'expertise_options': skills,
                    'expertise': skills[0]
                }
                print 'linkedin PROFILE: %s' % str(linkedin_profile)
                ds.update(linkedin_profile)
            linkedin_ds.update(update)
            return True
        return False

    @staticmethod
    def isLinkedinProfileEmpty():
        if not any(linkedin_ds.query(lambda ds: ds.get(p['key'], None)) for p in post_roles[1:]):
            return True
        return False


class LinkedInDialog(GridLayoutInt):
    __events__ = ('on_close', )
    userdata = ObjectProperty()
    title = StringProperty()
    line1 = StringProperty()
    line2 = StringProperty()
    allow_dismiss = True

    def __init__(self, **kwargs):
        super(LinkedInDialog, self).__init__(**kwargs)
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Linkedin login popup')
        #LogTestFairy('Linkedin login popup screen')

    def on_close(self, completed):
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Linkedin login popup closed')

    def _on_error(self, linkedin, reason=None):
        from modules.core.android_utils import Toast
        Toast('Linkedin login failed')
        self.allow_dismiss = True
        self.dispatch('on_close', False)

    def _on_complete(self, linkedin):
        from modules.core.android_utils import Toast
        Toast('Successfull Linkedin login')
        self.allow_dismiss = True
        self.dispatch('on_close', True)

    def button_clicked(self):
        from modules.core.android_utils import LogTestFairy
        LogTestFairy("Linkedin login button clicked")
        self.allow_dismiss = False
        self.linkedin = LinkedIn(
            on_complete=self._on_complete,
            on_error=self._on_error)
        self.linkedin.do_login()
        self.opacity = 0
