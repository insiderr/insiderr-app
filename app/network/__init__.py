

from kivy.utils import platform


def is_available():
    if platform == 'android':
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        theActivity = cast('com.insiderr.uix.InsiderrActivity', PythonActivity.mActivity)
        Context = autoclass('android.content.Context')
        connectivityManager = cast(
            'android.net.ConnectivityManager',
            theActivity.getSystemService(Context.CONNECTIVITY_SERVICE))
        activeNetworkInfo = connectivityManager.getActiveNetworkInfo()
        return activeNetworkInfo is not None and activeNetworkInfo.isConnected()
    return True
