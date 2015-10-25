from kivy.properties import ObjectProperty, BooleanProperty, NumericProperty
from . import InteractiveScreen
from widgets.bar import BarMiddleButton, BarMiddleImage
from utilities.itemfactory import ItemFactory
from post_themes import get_post_themes, get_post_theme, get_image_path, PostTheme
from widgets.menu import Menu, MenuItem
from widgets.items.userpost import UserPost, UserPostTemplate
from widgets.items.systempost import SystemPost, SystemPostTemplate
from widgets.items.template import ItemCallback
from utilities.unicode import remove_all_non_printables, convert_json_from_unicode
from api.streams.posts import Manager as PostsManager
from widgets.share import ShareDialog
from widgets.optionsmenu import OptionsMenu
from widgets.itemcontainer import ItemContainer
from functools import partial
from kivy.clock import Clock
from modules.core.android_utils import LogTestFairy
from utilities.voting import item_vote
from config import commented_ds, attitude_ds, favorites_ds, favs_data_ds, removed_ds, system_posts_path
from utilities.formatting import parse_timestring, datetime_format, get_color_from_hex
from utilities.timeutil import utc_to_local
from api.updates import get as get_updates
from os.path import join, splitext
from kivy.logger import Logger
from authentication import user_authenticated_on_session_start
from config import sys_posts_content


class PostsContainer(ItemContainer):
    item_factory = ItemFactory(6, UserPostTemplate)
    sys_item_factory = ItemFactory(1, SystemPostTemplate)
    vote_swipe_target = ObjectProperty()
    _vote_child = None
    _vote_widget = None

    def enqueue(self, key, data, index=0):
        self._resolve_data(data)
        if 'background' in data:
            # ugly hack to ensure non-posts won't creep in...
            super(PostsContainer, self).enqueue(key, data, index)

    def _resolve_data(self, data):
        data['content'] = remove_all_non_printables(data['content'])
        utc = parse_timestring(data.get('created', ''))
        data['created'] = utc_to_local(utc)
        if data.get('type', None) == 'sys':
            return self._resolve_sys_data(data)
        return self._resolve_user_data(data)

    def _resolve_sys_data(self, data):
        data['font_color'] = get_color_from_hex(data.get('font_color', 'FFFFFFFF'))
        background = data.get('background', 'unknown')
        color = PostTheme.get_color(background)
        if color:
            data['color'] = get_color_from_hex(color)
        else:
            _, ext = splitext(background)
            if ext in ['.jpg', '.png']:
                data['image'] = join(system_posts_path, background)

    def _resolve_user_data(self, data):
        background = data.get('background', 'unknown')
        theme = data.get('theme', 'unknown')
        icon_set = None
        image = None
        color = None
        t = get_post_theme(theme)
        if t:
            icon_set = t.get_iconset(background)
            color = PostTheme.get_color(background)
            if not color:
                image = get_image_path(t.key, background)
        if icon_set:
            data['icon_set'] = icon_set
        if image:
            data['image'] = image
        if color:
            data['color'] = get_color_from_hex(color)

    def _make_placeholder(self, data):
        if data and data.get('type', None) == 'sys':
            return SystemPost(
                size_hint=(1, None),
                data=data,
                factor=self._make_system_template,
                target=self.target)
        return UserPost(
            size_hint=(1, None),
            data=data,
            factor=self._make_template,
            gesture_target=self.target,
            target=self.target)

    def _make_template(self, data):
        key = data.get('key', None)
        if key:
            data['commented'] = commented_ds.query(lambda ds: key in ds)
            data['attitude'] = attitude_ds.query(lambda ds: ds.get(key, 'none'))
        item = self.item_factory.get_item(data)
        if not item:
            # crap we missed it...
            # no worries, we will get rescheduled
            return None
        return item

    def _make_system_template(self, data):
        item = self.sys_item_factory.get_item(data)
        if not item:
            # crap we missed it...
            # no worries, we will get rescheduled
            return None
        return item


class FeedScreen(ItemCallback, InteractiveScreen):
    __events__ = ('on_favs', 'on_item_selected', 'on_write_post', 'on_post_updated')

    loading = BooleanProperty(True)

    container = ObjectProperty()
    scrollview = ObjectProperty()
    async_feed = ObjectProperty()
    top_bar = ObjectProperty()
    menu_visible = BooleanProperty(False)

    stream = ObjectProperty()
    stream_system = None
    auto_update_interval = NumericProperty(15)
    last_update_hash = None

    sys_posts_count = 0

    def __init__(self, **kwargs):
        self.viewablebox = None
        self.feedInitialized = 0
        PostsManager.bind(
            connected=self._on_streams_connected)
        super(FeedScreen, self).__init__(**kwargs)

        def attach_events(*largs):
            self.scrollview.bind(
                on_stopped=self.refresh_scrollview,
                on_hit_bottom=self._get_prev_page,
                on_hit_top=self._get_next_page)

        if not self.scrollview:
            self.bind(scrollview=attach_events)
        else:
            attach_events()

    def _start_auto_update(self):
        Clock.schedule_interval(self._update, self.auto_update_interval)

    def _stop_auto_update(self):
        Clock.unschedule(self._update)

    def _on_streams_connected(self, manager, value):
        if value:
            if manager.streams:
                stream = None
                stream_system = None
                for s in manager.streams:
                    if not self.stream and s.title not in ['system', 'System']:
                        stream = s
                    elif not self.stream_system:
                        stream_system = s
                # order is important,  we have binding on stream
                self.stream_system = stream_system
                self.stream = stream
        else:
            self.stream = None

    def refresh_viewablewidgets(self, dt):
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

    def refresh_scrollview(self, scrollview, topx, topy, bottomx, bottomy):
        if self.feedInitialized or (scrollview and scrollview.scroll_y != 1):
            if self.feedInitialized==1:
                print('Scrolling feed')
                self.feedInitialized += 1
        else:
            self.feedInitialized = 1
            print('Feed initialized')

        if not self.viewablebox:
            #print 'Schedule next'
            Clock.schedule_once(self.refresh_viewablewidgets, 0.025)
        else:
            #print 'Reschedule!!!'
            Clock.unschedule(self.refresh_viewablewidgets)
            Clock.schedule_once(self.refresh_viewablewidgets, 0.250)
        self.viewablebox = (topx, topy, bottomx, bottomy)

    def on_favs(self):
        pass

    def on_write_post(self):
        pass

    def on_item_selected(self, item):
        pass

    def _on_page_add_system_post(self):
        if self.sys_posts_count >= len(sys_posts_content):
            return None
        systempost = None
        for s in sys_posts_content:
            if s['when'] == 'once' and not user_authenticated_on_session_start:
                s['when'] = 'done'
                systempost = s
                self.sys_posts_count += 1
                break
            if s['when'] == 'every':
                s['when'] = 'done'
                systempost = s
                self.sys_posts_count += 1
                break
            from widgets.linkedin import LinkedIn
            if s['when'] == 'linkedin' and LinkedIn.isLinkedinProfileEmpty():
                s['when'] = 'done'
                systempost = s
                self.sys_posts_count += 1
                break
        if not systempost:
            self.sys_posts_count = len(sys_posts_content)
        return systempost

    def _on_page(self, data, add_bottom=True, **kwargs):
        if not data:
            self.loading = False
            return

        # only insert when getting next page -- i.e. adding from the bottom
        systempost = self._on_page_add_system_post() if add_bottom else None

        removed = removed_ds.data()
        systempost_place = 0
        for pdata in data:
            systempost_place += 1
            if systempost and systempost_place == 4:
                self._add_system_post(
                    key='system_post_%s' % (self.sys_posts_count + 1),
                    index=0,
                    **systempost)

            post = pdata.get('post', None)
            hash = pdata.get('hash', None)
            if post:
                key = post.get('key', None)
                if key in removed:
                    continue
                d = convert_json_from_unicode(post)
                d['hash'] = hash
                if not key:
                    continue
                if self.stream_system and self.stream_system.key in d['channels']:
                    print 'Got system post'
                    self.stream_system.hash_bounds = hash
                    if len(d['content']) > 2 and d['content'][0] == '#':
                        print 'Systempost -- deep link'
                        key = d['content'][1:]
                        def on_get_deeplink(data, hash):
                            print 'Got deep links data'
                            if len(data) > 0:
                                wrapper = {'hash': hash, 'post': data[0]}
                                self._on_page([wrapper], add_bottom=False)
                        from api.items import get as getPostData
                        getPostData(keys=[key], on_items=on_get_deeplink)
                        continue
                    d['background'] = 'bkg.jpg'
                    d['when'] = 'once'
                    if d['role_text'].lower() == 'invite':
                        d['action'] = 'invite'
                        d['button'] = 'send invitation'
                    elif d['role_text'].lower() == 'linkedin':
                        d['action'] = 'linkedin'
                        d['button'] = 'Login with linkedin'
                    else:
                        d['action'] = 'close'
                    d['key'] = 'system_post_%s' % (self.sys_posts_count + 1)
                    d['index'] = -1
                    self._add_system_post(**d)
                    continue
                if add_bottom:
                    self.container.enqueue(key, d, index=0)
                else:
                    self.container.enqueue(key, d, index=-1)
        self.loading = False

    def _on_updates(self, data, hash=None):
        self.last_update_hash = hash
        removed = removed_ds.data()
        for pdata in data:
            post = pdata.get('obj', None)
            if post:
                key = post.get('key', None)
                if key and key not in removed:
                    self.container.enqueue(key, post)

    def _update(self, *largs):
        if not self.stream:
            return
        keys = self.container.get_widget_keys()
        self._get_next_page()
        args = {'hash': self.last_update_hash} if self.last_update_hash else {}
        get_updates(
            keys=keys,
            on_updates=self._on_updates,
            on_error=self.feed_network_error_message,
            **args)

    def _on_nextpage_getsystemposts(self, data, add_bottom=True):
        if self.stream_system and self.stream:
            if not self.stream_system.hash_bounds:
                self.stream_system.hash_bounds = self.stream.hash_bounds
            self.stream_system.get_next_page(
                on_page=partial(self._on_page, add_bottom=False),
                on_error=self.feed_network_error_message)
        self._on_page(data, add_bottom=add_bottom)

    def _get_page(self, *args):
        if self.stream:
            self.stream.get_current_page(
                on_page=self._on_nextpage_getsystemposts,
                on_error=self.feed_network_error_message)

    def _get_prev_page(self, *args):
        LogTestFairy('Feed prev page')
        if self.stream:
            self.stream.get_prev_page(
                on_page=self._on_page,
                on_error=self.feed_network_error_message)

    @staticmethod
    def feed_network_error_message(*args):
        return
        from modules.core.android_utils import Toast
        Toast('no network access')

    def _get_next_page(self, *args):
        print 'Feed next page'
        if self.stream:
            self.stream.get_next_page(
                on_page=partial(self._on_nextpage_getsystemposts, add_bottom=False),
                on_error=self.feed_network_error_message)

    def get_new_posts(self):
        self.scrollview.scroll_y = 1
        self._get_next_page()

    def on_pre_leave(self, *args):
        if self.top_bar:
            self.top_bar.color = (0, 0, 0, 1)
        self._stop_auto_update()

    def on_pre_enter(self, *args):
        if self.top_bar:
            self.top_bar.color = (0, 0, 0, 1)

    def _reload_stream(self, *args, **kwargs):
        if self.container.children:
            return
        if self.stream:
            self._get_page()
        else:
            self.bind(stream=self._get_page)

    def _add_system_post(self, key, index, **kwargs):
        from datetime import datetime
        kwargs.update({
            'type': 'sys',
            'key': key,
            'created': datetime.now().strftime(datetime_format),
            })
        self.container.enqueue('key', kwargs, index)

    def on_enter(self, *args):
        LogTestFairy('Open Feed')
        LogTestFairy('Feed screen')
        if self.container:
            self._reload_stream()
        else:
            self.bind(container=self._reload_stream)
        self._start_auto_update()

    def item_click(self, item, touch=None):
        if isinstance(item, SystemPost):
            from widgets.linkedin import LinkedIn
            Logger.info('SystemPost: %s clicked' % item.key)
            action = item.data.get('action', '')
            if action == 'invite':
                from modules.core. android_utils import ShareActivity
                from config import invite_url
                ShareActivity(invite_url, 'Send invite')
            elif action == 'linkedin':
                if LinkedIn.isLinkedinProfileEmpty():
                    linkedin = LinkedIn()
                    linkedin.do_login()
            def remove_sys_post(*largs):
                self.container.remove_widget(item)
            Clock.schedule_once(remove_sys_post, 3.0)
        else:
            self.dispatch('on_item_selected', item)

    def item_comments(self, item, touch):
        # comments icon does the same as clicking the post item
        self.dispatch('on_item_selected', item)

    def item_share(self, item, touch=None):
        ShareDialog.open(item)

    def _update_post_stats(self, key, attitude=None, *largs, **kwargs):
        if attitude:
            def update(ds):
                ds[key] = attitude
            attitude_ds.update(update)
            if attitude == 'like':
                def add_fav(ds):
                    ds.add(key)
                favorites_ds.update(add_fav)
            else: ##elif attitude == 'dislike':
                def remove_fav(ds):
                    if key in ds:
                        ds.remove(key)
                def remove_fav_data(ds):
                    if key in ds:
                        del ds[key]
                favorites_ds.update(remove_fav)
                favs_data_ds.update(remove_fav_data)
        if self.container:
            post = self.container.get_widget(key)
            if post:
                post.update_widget_data(kwargs)
        self.dispatch('on_post_updated', key, kwargs)

    def item_like(self, item, touch):
        item_vote(
            item=item,
            attitude='like',
            update_func=self._update_post_stats,
            testfairy_prefix='Feed')

    def item_dislike(self, item, touch):
        item_vote(
            item=item,
            attitude='dislike',
            update_func=self._update_post_stats,
            testfairy_prefix='Feed')

    def item_options(self, item, touch):
        LogTestFairy('Feed post menu')
        def share(dt, item):
            ShareDialog.open(item=item)
        def remove(opmenu, item_key):
            self._remove_post(item_key)
        OptionsMenu.open(
            item=item,
            on_share=Clock.create_trigger(partial(share, item=item), 0.025),
            on_removed=remove)

    def _remove_post(self, post_key):
        w = self.container.get_widget(post_key)
        if w:
            self.container.remove_widget(w)

    def on_post_updated(self, key, data):
        self.viewablebox = self.scrollview.get_viewbox()
        self.refresh_viewablewidgets(None)

    def add_gesture_animation(self, widget):
        if widget:
            self.scrollview.parent.add_widget(widget, 2)

    def remove_gesture_animation(self, widget):
        if widget:
            self.scrollview.parent.remove_widget(widget)

    def item_gesture_left(self, item, touch):
        print 'Gesture LEFT'
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Post vote gesture like')
        self.item_like(item, touch)

    def item_gesture_right(self, item, touch):
        print 'Gesture RIGHT'
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Post vote gesture dislike')
        self.item_dislike(item, touch)


class FeedBarMiddleButton(BarMiddleButton):
    def _create_menu(self):
        if not getattr(self, 'menu', None):
            self.menu = ThemesMenu()
            self.menu.bind(
                on_select=self._theme_selected,
                on_dismiss=self._update_parent)

    def _theme_selected(self, menu, item):
        self.title = item.title

    def _update_parent(self, dropdown=None, menu_visible=False):
        if self.parent.screen:
            self.parent.screen.menu_visible = menu_visible

    def on_release(self):
        self._create_menu()
        self.menu.open(self.parent, self.title)
        self._update_parent(menu_visible=True)


class FeedBarMiddleImage(BarMiddleImage):
    pass


class ThemeMenuItem(MenuItem):
    pass


class ThemesMenu(Menu):
    def __init__(self, **kwargs):
        super(ThemesMenu, self).__init__(**kwargs)
        self.populate()

    def populate(self):
        for theme in get_post_themes():
            self.add_widget(ThemeMenuItem(title=theme.title))


