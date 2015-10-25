from kivy.properties import ObjectProperty, StringProperty, NumericProperty, OptionProperty, BooleanProperty
from . import InteractiveScreen
from widgets.share import ShareDialog
from widgets.autosizemodal import AutosizeModal
from widgets.biditextinput import BidiTextInput
from widgets.layoutint import GridLayoutInt
from behaviors.interceptentertextinputbehavior import InterceptEnterTextInputBehavior
from behaviors.boundedtextinputbehavior import BoundedTextInputBehavior
from widgets.items.comment import Comment, CommentTemplate
from widgets.items.template import ItemCallback
from utilities.itemfactory import ItemFactory
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from theme import _scale_to_theme_dpi, anonymous_nick
from utilities.unicode import remove_all_non_printables
from api.comments import post as post_comment
from api.streams.comments import CommentsStream
from utilities.unicode import convert_json_from_unicode
from api.votes import post_up as post_vote_up, post_down as post_vote_down
from api.posts import get as get_post
from widgets.itemcontainer import ItemContainer
from utilities.formatting import parse_timestring
from post_themes import get_post_theme
from functools import partial
from utilities.timeutil import utc_to_local
from behaviors.hotspotbehavior import HotSpotBehavior
from modules.core.android_utils import LogTestFairy
from utilities.voting import item_vote
from utilities.keyboard import get_keyboard_top
from copy import copy
from widgets.items.userpost import UserPost
from config import commented_ds, attitude_ds, favorites_ds, post_roles, linkedin_ds
from kivy.logger import Logger
from widgets.modalmenu import ModalMenu
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior


placeholderimage = Image(source='data/commentholder.png')



class CommentTextInput(BoundedTextInputBehavior, InterceptEnterTextInputBehavior, BidiTextInput):
    #def get_def_min_height(self):
    #    return self.font_size + self.padding[0] + self.padding[2] + self.line_spacing
    #def_min_height = AliasProperty(get_def_min_height, None, bind=('line_height', 'line_spacing', 'padding'))
    pass


class CommentsContainer(ItemContainer):
    item_factory = ItemFactory(6, CommentTemplate)
    theme_key = StringProperty()
    theme = None

    def enqueue(self, key, data, index=0):
        self._resolve_data(data)
        if 'icon' in data:
            # ugly hack to ensure non-comments won't creep in...
            return super(CommentsContainer, self).enqueue(key, data, index)

    def _resolve_data(self, data):
        utc = parse_timestring(data.get('created', ''))
        data['time'] = utc_to_local(utc)
        data['content'] = remove_all_non_printables(data['content'])
        #data['role'] = data.get('role', post_roles[0]['key']) or post_roles[0]['key']
        #data['role_text'] = data.get('role_text', anonymous_nick) or anonymous_nick
        icon = None
        if self.theme:
            data['theme'] = self.theme.key
            icon_index = data.get('icon', '')
            if isinstance(icon_index, int):
                icon, icolor = self.theme.get_icon_tuple(icon_index)
        if icon:
            data['icon'] = icon
            data['icon_color'] = icolor
        elif 'icon' in data:
            # if no icon was parsed, make sure to remove it and force
            # the widget to load the default icon
            del data['icon']

    def on_theme_key(self, *largs):
        self.theme = get_post_theme(largs[-1])

    def _make_placeholder(self, data):
        return Comment(
            size_hint=(1, None),
            height=_scale_to_theme_dpi(90),
            data=data,
            placeholder_texture=placeholderimage.texture,
            factor=self._make_template,
            gesture_target=self.target,
            gesture_anim_height=_scale_to_theme_dpi(70),
            target=self.target)

    def _make_template(self, data):
        key = data.get('key', None)
        if key:
            data['attitude'] = attitude_ds.query(lambda ds: ds.get(key, 'none'))
        item = self.item_factory.get_item(data)
        if not item:
            # crap we missed it...
            # no worries, we will get rescheduled
            return None
        return item

    def _add_widget_impl(self, widget, index):
        index = 0
        for c in self.children:
            if widget.time > c.time:
                break
            index += 1
        super(CommentsContainer, self)._add_widget_impl(widget, index)


class CommentsRoleEntry(ToggleButtonBehavior, GridLayoutInt):
    role = StringProperty()
    role_desc = StringProperty()


class CommentsRoleMenu(ModalMenu):
    __events__ = ('on_selected',)
    def __init__(self, selected_role=None, **kwargs):
        super(CommentsRoleMenu, self).__init__(**kwargs)
        if not selected_role:
            selected_role = post_roles[0]['key']
        for p in post_roles:
            key = p['key']
            e = CommentsRoleEntry(
                role=key,
                role_desc=linkedin_ds.query(lambda ds: ds.get(key, '')),
                state='down' if (key == selected_role) else 'normal')
            if e.role_desc != 'unknown':
                self.add_widget(e)

    def button_clicked(self, item):
        self.dispatch('on_selected', item.role)
        super(CommentsRoleMenu, self).button_clicked(item)

    def on_selected(self, role):
        pass


class CommentsScreen(ItemCallback, InteractiveScreen):
    __events__ = ('on_close', 'on_comment')

    post_box = ObjectProperty()
    comments_container = ObjectProperty()
    comment_textinput = ObjectProperty()
    textinput_layout = ObjectProperty()
    scrollview = ObjectProperty()
    userpost_icon_set = StringProperty()
    status = OptionProperty('loading', options=('loading', 'empty', 'populated'))

    post = ObjectProperty()
    post_key = StringProperty()
    post_theme = StringProperty()
    textinput_collapsed_height = NumericProperty(0)

    auto_update_interval = NumericProperty(15)

    input_active = BooleanProperty(False)
    keyboard_top = NumericProperty(0)

    #role = OptionProperty(DEFAULT_ROLE, options=(p['key'] for p in post_roles))
    role_menu_open = BooleanProperty(False)
    _role_menu = None

    _input_interaction = False

    userpost = None

    def __init__(self, **kwargs):
        super(CommentsScreen, self).__init__(**kwargs)
        self.viewablebox = None
        if not self.scrollview:
            self.bind(scrollview=(lambda *instance: self.scrollview.bind(on_stopped=self.refresh_scrollview)))
        else:
            from kivy import platform
            if platform in ['ios', 'macosx']:
                from kivy.uix.relativelayout import RelativeLayout
                from kivy.core.window import Window
                w = RelativeLayout(size_hint=(1, None), height=0.02*Window.height)
                w.height = 0.02*Window.height
                self.scrollview.children[0].add_widget(w, index=len(self.scrollview.children[0].children))

            self.scrollview.bind(on_stopped=self.refresh_scrollview)

    def on_input_active(self, instance, value):
        if value:
            # We need to make sure we don't do this when we enter the screen otherwise
            # the keyboard will pop open... This way, it'll only be really assigned once.
            # Any assignment of the same value later on will simply be ignored.
            self.keyboard_top = get_keyboard_top()

    def on_comment_textinput(self, instance, value):
        value.bind(focus=self._on_textinput_focus)

    def _on_textinput_focus(self, instance, value):
        if value:
            self.input_active = True
        elif not self._input_interaction:
            self.input_active = False
        self._input_interaction = False

    def on_touch_down(self, touch):
        tl = self.textinput_layout
        p = tl.to_widget(*self.to_window(*touch.pos))
        if tl.collide_point(*p):
            self._input_interaction = True
        super(CommentsScreen, self).on_touch_down(touch)

    def on_manager(self, *largs):
        feed_screen = self.manager.get_screen('feed')
        self.userpost = up = feed_screen.container._make_placeholder(None)
        up.width = feed_screen.container.width
        up.bind(height=self.post_box.setter('height'))
        self.post_box.add_widget(up, len(self.post_box.children))

    def set_post_data(self, data):
        self.post_key = data.get('key', 'unknown')
        self.userpost_icon_set = data.get('icon_set', 'light')
        self.post_theme = data.get('theme', 'unknown')

        self.ref_post = None
        feed_screen = self.manager.get_screen('feed')
        feed_screen.container._resolve_data(data)
        self.userpost.update_widget(data, ignore_old_data=True)
        feed_screen.bind(on_post_updated=self._update_userpost_data)

    def _role_selected(self, menu, role):
        self.role = role

    def _role_menu_dismissed(self, menu):
        self.role_menu_open = False
        self.comment_textinput.focus = True

    def update_role_desc_linkedin(self, dlg, completed):
        def hide_keyb(dt):
            self.comment_textinput.focus = True
            self.comment_textinput.focus = False
        Clock.schedule_once(hide_keyb, 1)
        if completed:
            self.toggle_role_menu(dlg.userdata)

    def _open_linkedin_popup(self, button):
        from widgets.autosizemodal import AutosizeModal
        from widgets.linkedin import LinkedInDialog

        def dismissed(*args):
            from kivy import platform
            if platform != 'ios':
                self.comment_textinput.focus = True

        dlg = LinkedInDialog(
            userdata=button,
            title="Now that you're in",
            line1="Remain anonymous but spice up your\ncomments by adding linkedin credentials",
            line2="Don't worry\nyou will stay completely anonymous",
            on_close=self.update_role_desc_linkedin)
        def open(dt):
            AutosizeModal(
                widget=dlg,
                on_dismiss=dismissed
            ).open()
        Clock.schedule_once(open, 0)

    def toggle_role_menu(self, button):
        if not self.input_active:
            self.comment_textinput.focus = True
        else:
            if self.role_menu_open:
                if self._role_menu:
                    self._role_menu.dismiss()
            else:
                if not any(linkedin_ds.query(lambda ds: ds.get(p['key'], None)) for p in post_roles[1:]):
                    # no linkedin data
                    self._open_linkedin_popup(button)
                    return
                self.role_menu_open = True
                if not self._role_menu:
                    w = CommentsRoleMenu(
                        selected_role=self.role,
                        on_selected=self._role_selected)
                    self._role_menu = AutosizeModal(
                        widget=w,
                        background_color=(0,0,0,0),
                        force_pos={'y': self.textinput_layout.top, 'x': button.x},
                        on_dismiss=self._role_menu_dismissed)
                self._role_menu.open()
        self._input_interaction = False

    def _update_userpost_data(self, feed_screen, key, data):
        if self.userpost and self.userpost.key == key:
            self.userpost.update_widget(data)

    def _update_userpost_texture(self, *largs):
        self.userpost.update_texture(largs[-1])

    def set_post(self, post):
        self.post_key = post.key
        self.userpost_icon_set = post.icon_set
        self.post_theme = post.theme

        self.ref_post = post
        self.userpost.update_widget_data(post.data, ignore_old_data=True)
        self.userpost.update_texture(post.texture)
        post.bind(texture=self._update_userpost_texture)
        feed_screen = self.manager.get_screen('feed')
        self.userpost.attach_hotspots_from(
            post,
            target=feed_screen,
            instance=post,
            dont_override=['item_click'])
        # maybe we should restore them?!
        self.userpost._gesture_target = self


    def on_close(self):
        pass

    @staticmethod
    def feed_network_error_message(*args):
        from modules.core.android_utils import Toast
        Toast('no network access')

    def _comment_created(self, **kwargs):
        num_comments = len(self.comments_container.children)
        from time import time
        scheduler_started = time()
        def _update(ds):
            ds.add(self.post_key)
        def _scrollbottom(ds):
            numc = len(self.comments_container.children)
            if numc < 1:
                return
            if num_comments != numc:
                self.scrollview.scroll_y = 0
            elif time() - scheduler_started<3:
                # reschedule
                Clock.schedule_once(_scrollbottom, 0.250)

        commented_ds.update(_update)
        favorites_ds.update(_update)
        self.update_post()
        self.stream.get_page(on_page=self._on_page, on_error=self.feed_network_error_message)
        Clock.schedule_once(_scrollbottom, 0.050)

    def on_comment(self):
        ti = self.comment_textinput
        if ti.text:
            post_comment(
                post_key=self.post_key,
                content=ti.text,
                role="",
                role_text="",
                on_created=self._comment_created)
        ti.text = ''
        ti.focus = False
        self.input_active = False

    def _start_auto_update(self):
        Clock.schedule_interval(self._get_current_page, self.auto_update_interval)

    def _stop_auto_update(self):
        Clock.unschedule(self._get_current_page)

    def on_pre_enter(self, *args):
        super(CommentsScreen, self).on_pre_enter(*args)
        self.scrollview.scroll_y = 1
        LogTestFairy('Open Post')
        LogTestFairy('Post screen')
        self.comment_textinput.text = ''
        self.comment_textinput.last_line_rtl = False
        self.comment_textinput._refresh_hint_text()
        self.clear_content()

    def _get_current_page(self, *largs):
        self.stream.get_current_page(on_page=self._on_page, on_error=self.feed_network_error_message)

    def on_enter(self, *args):
        self.stream = CommentsStream(post_key=self.post_key, on_error=self.feed_network_error_message)
        self._get_current_page()
        self._start_auto_update()

    def on_pre_leave(self, *args):
        self._stop_auto_update()
        if self.ref_post:
            self.ref_post.unbind(texture=self._update_userpost_texture)
            self.ref_post = None
        feed_screen = self.manager.get_screen('feed')
        feed_screen.unbind(on_post_updated=self._update_userpost_data)
        self.scrollview.scroll_y = 1
        self.scrollview.effect_y.value = 1

    def clear_content(self):
        #self.role = DEFAULT_ROLE
        if self.comments_container:
            self.comments_container.clear_widgets()
            self.status = 'loading'

    def on_leave(self, *args):
        LogTestFairy('Close Post')
        # No need to keep them, we'll reload anyway
        self.clear_content()

    def _on_page(self, data, **kwargs):
        c = self.comments_container
        if c:
            numcomments = len(c.children)
            update_numcomments = False
            for cdata in reversed(data):
                updated = c.enqueue(
                    cdata.get('key', None),
                    convert_json_from_unicode(cdata))
                if updated:
                    numcomments += 1
                    update_numcomments = True
            self.status = 'populated' if data else 'empty'
            if update_numcomments:
                post_data = {'comment_count': int(numcomments)}
                if self.ref_post:
                    self.ref_post.update_widget(post_data)
                else:
                    self.userpost.update_widget(post_data)

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
        self.comments_container.refresh_widgets(topx, topy, bottomx, bottomy, self.scrollview.effect_y.velocity, self.scrollview)
        self.viewablebox = None
        self.scrollview.canvas.ask_update()

    def refresh_scrollview(self, scrollview, topx, topy, bottomx, bottomy):
        if not self.viewablebox:
            #print 'Schedule next'
            Clock.schedule_once(self.refresh_viewablewidgets, 0.025)
        else:
            #print 'Reschedule!!!'
            Clock.unschedule(self.refresh_viewablewidgets)
            Clock.schedule_once(self.refresh_viewablewidgets, 0.250)
        self.viewablebox = (topx, topy, bottomx, bottomy)

    def share(self):
        m = AutosizeModal(widget=ShareDialog())
        m.open()

    def do_exit_input(self):
        if self.input_active:
            if self.role_menu_open and self._role_menu:
                self._role_menu.dismiss()
                return True
            elif self.comment_textinput.focus:
                self.comment_textinput.focus = False
                return True

    def _update_comment_stats(self, key, attitude=None, **kwargs):
        if attitude:
            def update(ds):
                ds[key] = attitude
            attitude_ds.update(update)
        if self.comments_container:
            comment = self.comments_container.get_widget(key)
            if comment:
                comment.update_widget_data(kwargs)

    def item_like(self, item, touch):
        item_vote(
            item=item,
            attitude='like',
            update_func=self._update_comment_stats,
            testfairy_prefix='Comment')

    def item_dislike(self, item, touch):
        item_vote(
            item=item,
            attitude='dislike',
            update_func=self._update_comment_stats,
            testfairy_prefix='Comment')

    def update_post(self, *args):
        LogTestFairy('Comment added')
        def _do_update(data):
            feed_screen = self.manager.get_screen('feed')
            feed_screen.container._resolve_data(data)
            if self.ref_post:
                self.ref_post.update_widget(data)
            else:
                self.userpost.update_widget(data)
        get_post(
            post_key=self.post_key,
            on_post=_do_update)

    def add_gesture_animation(self, widget):
        if widget:
            self.scrollview.parent.add_widget(widget, 1)

    def remove_gesture_animation(self, widget):
        if widget:
            self.scrollview.parent.remove_widget(widget)

    def item_gesture_left(self, item, touch):
        print 'Gesture LEFT'
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Comment vote gesture like')
        self.item_like(item, touch)

    def item_gesture_right(self, item, touch):
        print 'Gesture RIGHT'
        from modules.core.android_utils import LogTestFairy
        LogTestFairy('Comment vote gesture dislike')
        self.item_dislike(item, touch)
