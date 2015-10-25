from kivy import platform


def get_mac_addr():
    if platform == 'android':
        from jnius import autoclass, cast
        Context = autoclass('android.content.Context')
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        theActivity = PythonActivity.mActivity

        wifiManager = cast('android.net.wifi.WifiManager',
                           theActivity.getSystemService(Context.WIFI_SERVICE))
        macAddr = wifiManager.getConnectionInfo().getMacAddress()
        if macAddr:
            # remove ':' chars from MAC address
            macAddr = macAddr.translate(None, ':')
        else:
            from uuid import getnode
            macAddr = '%X' % getnode()
    else:
        from uuid import getnode
        macAddr = '%X' % getnode()

    return macAddr