from kivy.properties import ObjectProperty, BooleanProperty, OptionProperty
from . import InteractiveScreen
from utilities.itemfactory import ItemFactory
from post_themes import get_post_theme
from kivy.utils import get_color_from_hex
from widgets.items.userpostfav import UserPostFavTemplate
from kivy.clock import Clock
from kivy.uix.image import Image
from theme import favs_userpost_height
from widgets.itemcontainer import ItemContainer
from widgets.items.userpostfav import UserPostFav
from utilities.unicode import remove_all_non_printables
from widgets.autosizemodal import AutosizeModal
from widgets.feedback import FeedbackDialog
from widgets.modalmenu import ModalMenu
from widgets.items.template import ItemCallback
from api.updates import get as get_updates
from api.items import get as get_items
from modules.core.android_utils import LogTestFairy
from kivy.logger import Logger

from config import favs_data_ds, favorites_ds


class FavsContainer(ItemContainer):
    item_factory = ItemFactory(5, UserPostFavTemplate)
    placeholderimage = Image(source='data/commentholder.png')
    _reordered_once = False

    def enqueue(self, key, data, index=0):
        self._resolve_data(key, data)
        super(FavsContainer, self).enqueue(key, data, index)

    def on_queue_empty(self):
        super(ItemContainer, self).on_queue_empty()
        if not self._reordered_once:
            self.reorder_widgets()
            self._reordered_once = True

    def reorder_widgets(self, top_keys=[]):
        # top are those moved to top, in the same order as requested
        topc = [self.get_widget(key) for key in reversed(top_keys)]
        # middle are those still unread, in their current order
        middlec = [c for c in self.children if c.key not in top_keys and c.changed]
        # bottom are those already read, sorted by creation time
        bottomc = [c for c in self.children if c.key not in top_keys and not c.changed]
        bottomc.sort(key=lambda w: w.time)

        self.children = list(bottomc + middlec + topc)
        self._trigger_layout()

    def _was_read(self, key):
        cached = favs_data_ds.query(lambda ds: ds.get(key, None))
        return cached and cached.get('read', True)

    def _set_read(self, keys, value):
        def update(ds):
            for key in keys:
                ds[key] = {'read': value}
        favs_data_ds.update(update)
        # reorder widgets (those set to `read` already have their prop changed,
        # which will affect reordering
        self.reorder_widgets()

    def _resolve_data(self, key, data):
        data['time'] = data.get('created', '')
        if key:
            # widget is `changed` (meaning unread) if it exists (this is an update with new data) or
            # if it was previously read
            data['changed'] = not self._was_read(key)
        data['content'] = remove_all_non_printables(data['content'])
        data['color'] = self._resolve_color(data)
        return key

    def _resolve_color(self, data):
        theme = get_post_theme(data.get('theme', 'unknown'))
        color = 'ffffff'
        if theme:
            background = data['background']
            color = theme.get_color(background)
            if not color:
                color = theme.get_color_by_image(background)
        return get_color_from_hex(color)

    def _make_placeholder(self, data):
        return UserPostFav(
            size_hint=(1, None),
            height=favs_userpost_height,
            data=data,
            placeholder_texture=self.placeholderimage.texture,
            factor=self._make_template,
            target=self.target)

    def _make_template(self, data):
        item = self.item_factory.get_item(data)
        if not item:
            # crap we missed it...
            # no worries, we will get rescheduled
            return None
        return item


class AboutDialog(ModalMenu):
    __events__ = ('on_eula', 'on_legal', 'on_privacy')

    def __init__(self, **kwargs):
        LogTestFairy('About menu')
        super(AboutDialog, self).__init__(**kwargs)

    @classmethod
    def open(cls, **kwargs):
        w = AboutDialog(**kwargs)
        AutosizeModal(widget=w, **kwargs).open()

    def button_clicked(self, touch):
        super(AboutDialog, self).button_clicked(touch)
        action = touch.action
        LogTestFairy('About dialog menu pressed %s' % action)
        if self.is_event_type(action):
            self.dispatch(action)
        self.dispatch('on_close')

    def on_eula(self):
        from modules.core.android_utils import OpenUrlActivity
        OpenUrlActivity('http://insiderr.com')

    def on_privacy(self):
        from modules.core.android_utils import OpenUrlActivity
        OpenUrlActivity('http://insiderr.com')

    def on_legal(self):
        from modules.core.android_utils import OpenUrlActivity
        OpenUrlActivity('http://insiderr.com')


class FavDialog(ModalMenu):
    __events__ = ('on_mark_all', 'on_feedback', 'on_invite', 'on_notifications', 'on_rate', 'on_about', 'on_linkedin', 'on_exit')

    notify = BooleanProperty(True)

    def __init__(self, **kwargs):
        LogTestFairy('Favorite menu')
        super(FavDialog, self).__init__(**kwargs)

    @classmethod
    def open(cls, **kwargs):
        w = FavDialog(**kwargs)
        AutosizeModal(widget=w, **kwargs).open()

    def button_clicked(self, touch):
        action = touch.action
        LogTestFairy('Favorite menu pressed %s' % action)
        if self.is_event_type(action):
            self.dispatch(action)
        if action != 'on_about':
            self.dispatch('on_close')

    def on_mark_all(self):
        pass

    def on_feedback(self):
        FeedbackDialog.open(
            force_pos={'top': self.top},
            background_color=(0, 0, 0, .6))

    def on_invite(self):
        from modules.core. android_utils import ShareActivity
        from config import invite_url
        ShareActivity(invite_url, 'Send invite')

    def on_notifications(self):
        pass

    def on_rate(self):
        from modules.core. android_utils import OpenUrlActivity
        from config import rate_url
        OpenUrlActivity(rate_url)

    def on_about(self):
        AboutDialog.open(background_color=(0, 0, 0, .2))

    def on_linkedin(self):
        def updated(*largs):
            from modules.core.android_utils import Toast
            Toast('Linkedin profile updated')
        from widgets.linkedin import LinkedIn
        self.linkedin = LinkedIn(on_complete=updated)
        self.linkedin.do_login()

    def on_exit(self):
        # Exit explicitly
        from kivy.base import stopTouchApp
        stopTouchApp()


class FavsScreen(ItemCallback, InteractiveScreen):
    __events__ = ('on_close', 'on_menu', 'on_item_selected')

    container = ObjectProperty()
    scrollview = ObjectProperty()

    status = OptionProperty('loading', options=('loading', 'empty', 'populated'))

    notify = True

    last_sample_hash = None

    load_failed_timeout = 5

    fake_click_for_item = None

    def __init__(self, **kwargs):
        super(FavsScreen, self).__init__(**kwargs)
        self.viewablebox = None
        if not self.scrollview:
            self.bind(scrollview=(lambda *instance: self.scrollview.bind(on_stopped=self.refresh_scrollview)))
        else:
            self.scrollview.bind(on_stopped=self.refresh_scrollview)

    def on_close(self):
        pass

    def _update_sample_hash(self, hash):
        self.last_sample_hash = max(hash, self.last_sample_hash)

    def fake_click_if_required(self, key, data):
        if self.fake_click_for_item and key == self.fake_click_for_item:
            self.fake_click_for_item = None
            self.item_click(item=None, touch=None, data_override=data)

    def _on_items(self, data, hash, **kwargs):
        self._update_sample_hash(hash)
        if data:
            self.status = 'populated'
            for pdata in data:
                key = pdata.get('key', None)
                self.container.enqueue(
                    key,
                    pdata,
                    index=-1)
                self.fake_click_if_required(key, pdata)
        else:
            self.status = 'empty'

    def _on_updates(self, data, hash, **kwargs):
        self._update_sample_hash(hash)
        if data:
            objs = [d.get('obj', None) for d in data]
            hashes = [d.get('hash', None) for d in data]
            keys = [o.get('key', None) for o in objs]
            self.container._set_read([key for key in keys if key], False)
            self.container.reorder_widgets(
                top_keys=zip(*sorted(zip(keys, hashes), key=lambda t: t[1], reverse=True))[0])
            for key, obj in zip(keys, objs):
                if key and obj:
                    self.container.enqueue(key, obj)
                self.fake_click_if_required(key, obj)

    def on_leave(self):
        LogTestFairy('Close Favorites')

    def _on_no_favorites(self, *args):
        self.status = 'empty'
        from modules.core.android_utils import Toast
        Toast('favorites timeout')

    def on_status(self, instance, value):
        if value == 'populated':
            Clock.unschedule(self._on_no_favorites)

    def on_pre_enter(self):
        LogTestFairy('Open Favorites')
        LogTestFairy('Favorites screen')

        fav_keys = favorites_ds.data()
        existing_keys = None

        # Remove all non-favorites from container
        c = self.container
        if c:
            keys = set(c.get_widget_keys())
            for key in (keys - fav_keys):
                c.remove_widget(c.get_widget(key))
            existing_keys = keys.intersection(fav_keys)

        if not c or not c.children:
            self.status = 'loading'

        if not fav_keys:
            self.status = 'empty'
        else:
            self.container.reorder_widgets()
            new_keys = (fav_keys - existing_keys)
            if new_keys:
                get_items(
                    keys=new_keys,
                    on_items=self._on_items)
                Clock.schedule_once(self._on_no_favorites, self.load_failed_timeout)

            if existing_keys:
                get_updates(
                    keys=existing_keys,
                    hash=self.last_sample_hash,
                    on_updates=self._on_updates)
        print('Fav on_pre_enter - done')

    def _mark_all_read(self, *largs):
        self.set_items_read(self.container.children[:])

    def _create_menu(self, top=0, right=0):
        if not getattr(self, 'menu', None):
            FavDialog.open(
                notify=self.notify,
                on_mark_all=self._mark_all_read,
                on_notifications=self._toggle_notify,
                force_pos={'top': top - 10, 'right': right},
                background_color=(0, 0, 0, .2))

    def on_menu(self, button):
        self._create_menu(top=button.y, right=button.right)

    def refresh_scrollview(self, scrollview, topx, topy, bottomx, bottomy):
        if not self.viewablebox:
            #print 'Schedule next'
            Clock.schedule_once(self.refresh_viewablewidgets, 0.025)
        else:
            #print 'Reschedule!!!'
            Clock.unschedule(self.refresh_viewablewidgets)
            Clock.schedule_once(self.refresh_viewablewidgets, 0.250)
        self.viewablebox = (topx, topy, bottomx, bottomy)

    def refresh_viewablewidgets(self, *args):
        if not self.viewablebox:
            return
        if abs(self.scrollview.effect_y.velocity) > self.scrollview.min_stop_velocity:
            #print 'wait til next time speed -- %s' % self.scrollview.effect_y.velocity
            Clock.schedule_once(self.refresh_viewablewidgets, 0.200)
            return
        self.viewablebox = self.scrollview.get_viewbox()
        #print 'refreshing widget -- %s' % str(self.viewablebox)
        topx, topy, bottomx, bottomy = self.viewablebox
        self.container.refresh_widgets(topx, topy, bottomx, bottomy, self.scrollview.effect_y.velocity, self.scrollview)
        self.viewablebox = None
        self.scrollview.canvas.ask_update()

    def item_click(self, item, touch=None, data_override=None):
        if item:
            self.set_items_read([item])
            data = item.data.copy()
        elif data_override:
            data = data_override.copy()
        else:
            return
        del data['color']
        self.dispatch('on_item_selected', data)

    def set_items_read(self, items):
        changed_items = [item for item in items if item.changed]
        for item in changed_items:
            item.set_changed(False)
        self.container._set_read(
            [i.key for i in changed_items],
            True)

    def on_item_selected(self, item_data):
        pass

    def _toggle_notify(self, *largs):
        self.notify = not self.notify
        from modules.core.android_utils import Toast
        if self.notify:
            Toast('notifications enabled')
        else:
            Toast('notifications disabled')
