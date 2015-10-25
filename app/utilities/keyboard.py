from theme import _scale_to_theme_dpi


_keyboard_top_absolute = -1
def get_keyboard_top():
    from kivy import platform
    global _keyboard_top_absolute
    if _keyboard_top_absolute > 0:
        return _keyboard_top_absolute

    if platform == 'android':
        import android
        #from kivy.clock import Clock
        from kivy.logger import Logger
        from time import sleep

        class Target:
            password = False
            keyboard_suggestions = True
        target = Target()
        android.show_keyboard(target, 'text')
        for i in range(50):
            keyboard_top = android.get_keyboard_height()
            Logger.info('Theme: android get_keyboard_height return %s' % keyboard_top)
            try:
                _keyboard_top_absolute = int(keyboard_top)
            except Exception:
                pass
            if _keyboard_top_absolute > 0:
                break
            sleep(0.025)
    elif platform == 'ios':
        from kivy.core.window import Window
        if hasattr(Window, 'keyboard_height') and (Window.keyboard_height > 0):
            _keyboard_top_absolute =  Window.keyboard_height
            print 'HAS KEYB HEIGHT %s' % _keyboard_top_absolute
        else:
            #from kivy.metrics import Metrics
            _keyboard_top_absolute = int(Window.height*0.3805) #288.0*Metrics.density
            print 'DEF KEYB HEIGHT %s' % _keyboard_top_absolute
    else:
        _keyboard_top_absolute = _scale_to_theme_dpi(300)


    return _keyboard_top_absolute