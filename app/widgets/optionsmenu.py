from kivy.properties import ObjectProperty, BooleanProperty
from widgets.autosizemodal import AutosizeModal
from widgets.modalmenu import ModalMenu
from api.flags import post as post_flag
from modules.core.android_utils import LogTestFairy
from config import favorites_ds, favs_data_ds, removed_ds


def remove_post_from_favs(key):
    def remove(ds):
        if key in ds:
            ds.remove(key)
    favorites_ds.update(remove)


def add_post_to_favs(key):
    def add(ds):
        ds.add(key)
    favorites_ds.update(add)


def remove_post_from_fav_data(key):
    def remove(ds):
        if key in ds:
            del ds[key]
    favs_data_ds.update(remove)


def remove_post(key):
    def update(ds):
        ds.add(key)
    removed_ds.update(update)
    remove_post_from_favs(key)
    remove_post_from_fav_data(key)


class OptionsMenu(ModalMenu):
    __events__ = ('on_share', 'on_removed')
    item = ObjectProperty()
    favorite = BooleanProperty(False)
    item_key = None

    def __init__(self, **kwargs):
        LogTestFairy('Post option menu')
        super(OptionsMenu, self).__init__(**kwargs)
        if self.item:
            self.item_key = getattr(self.item, 'key', None)
            if self.item_key:
                self.favorite = favorites_ds.query(lambda ds: self.item_key in ds)

    @staticmethod
    def open(on_share=None, **kwargs):
        w = OptionsMenu(**kwargs)
        if on_share:
            w.bind(on_share=on_share)
        AutosizeModal(widget=w, **kwargs).open()

    def button_clicked(self, item):
        super(OptionsMenu, self).button_clicked(item)
        action = item.action
        LogTestFairy('Post option menu pressed %s' % action)
        if action == 'share':
            self.dispatch('on_share', self.item)
        elif action == 'favorite':
            self._toggle_favorite()
        elif action == 'remove':
            from modules.core.android_utils import Toast
            Toast('post removed')
            if self.item_key:
                self.dispatch('on_removed', self.item_key)
        elif action == 'flag':
            from modules.core.android_utils import Toast
            Toast('post flagged')
            if self.item_key:
                post_flag(self.item_key)
                self.dispatch('on_removed', self.item_key)

    def _toggle_favorite(self):
        from modules.core.android_utils import Toast
        if self.favorite:
            remove_post_from_favs(self.item_key)
            remove_post_from_fav_data(self.item_key)
            Toast('removed from favorites')
        else:
            add_post_to_favs(self.item_key)
            Toast('added to favorites')
        # Don't update since the modal is closing anyway
        # self.favorite = not self.favorite

    def on_share(self, item):
        pass

    def on_removed(self, item_key):
        if item_key:
            remove_post(item_key)