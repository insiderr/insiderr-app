from kivy.core.window import Window
from config import keys as config_keys


class KeyManagerBehavior(object):
    def __init__(self, **kwargs):
        super(KeyManagerBehavior, self).__init__(**kwargs)
        Window.bind(on_key_down=self.on_key_down)

    def on_key_down(self, instance, key, keycode, *largs):
        cs = self.root.manager.current_screen
        if key == config_keys['back']:
            cs.trigger_back()
            return True
        elif key == config_keys['load']:
            load = getattr(cs, 'populate', None)
            if load and hasattr(load, '__call__'):
                load()
            return True
