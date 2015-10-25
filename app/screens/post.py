from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from screens import InteractiveScreen
from kivy.utils import get_color_from_hex, get_hex_from_color
from kivy.uix.widget import Widget
from modules.image.img_opencv import AsyncImageOpenCV
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.properties import ListProperty
from kivy.graphics import Color, Rectangle
from widgets.imagebutton import ImageToggleButton
from widgets.layoutint import GridLayoutInt
from post_themes import get_post_themes, get_post_theme, get_thumb_path, get_image_path
from theme import back_color, post_themeicon_container_item_extra_spacing, \
    post_roleicon_bubble_bottom_spacing, post_roleicon_bubble_container_min_distance, anonymous_nick
from functools import partial
from behaviors.togglebuttongroupbehavior import ToggleButtonGroupBehavior
from kivy.logger import Logger
from kivy.clock import Clock
from api.posts import post
from api.streams.posts import Manager as PostsManager
from config import feed_placeholder, comment_length_limit, favorites_ds, linkedin_ds, post_roles
from modules.core.android_utils import LogTestFairy
from kivy.animation import Animation
from utilities.formatting import format_vowel
from widgets.bidilabel import BidiLabel


DEFAULT_THEME = 'general'



def get_linkedin_data(role):
    if not linkedin_ds.data():
        if role == 'anonymous':
            return anonymous_nick
        return ''
    return linkedin_ds.query(lambda ds: ds.get(role, ''))


class BackgroundThumb(ToggleButtonBehavior):
    def __init__(self, **kwargs):
        super(BackgroundThumb, self).__init__(**kwargs)
        self.group = 'theme_thumbs'

    def on_state(self, instance, value):
        self.disabled = (value == 'down')
        if self.disabled:
            with self.canvas.after:
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.x, self.y), size=(self.width, 5))
                Rectangle(pos=(self.x+self.width-5, self.y), size=(5, self.height))
                Rectangle(pos=(self.x, self.y), size=(5, self.height))
                Rectangle(pos=(self.x, self.y+self.height-5), size=(self.width, 5))
        else:
            self.canvas.after.clear()
        self.canvas.ask_update()


class BackgroundColor(BackgroundThumb, Widget):
    color = StringProperty()


class BackgroundImage(BackgroundThumb, AsyncImageOpenCV):
    thumb_key = StringProperty()


# class ThemeIcon(ToggleButtonGroupBehavior, ImageToggleButton):
#     key = StringProperty()
#     icon_set = StringProperty()
#
#     def __init__(self, **kwargs):
#         super(ThemeIcon, self).__init__(**kwargs)


class RoleLabel(BidiLabel):
    pass


class RoleBubble(GridLayoutInt):
    text = StringProperty()
    icon_set = StringProperty()
    arrow_x = NumericProperty()
    values = ListProperty([])
    carousel = ObjectProperty()
    font_color = ListProperty([0, 0, 0, 1])

    def __init__(self, **kwargs):
        super(RoleBubble, self).__init__(**kwargs)
        self.size = 1, 1

    def _adjust_carousel_size(self, instance, value):
        w, h = value
        self.carousel.size = map(max, self.carousel.size, value)
        self.update_minimum_size()

    def on_values(self, *args):
        if self.carousel:
            self._populate_carousel()

    def _current_slide_changed(self, instance, value):
        self.text = value.text

    def on_carousel(self, *args):
        self.carousel.bind(current_slide=self._current_slide_changed)
        self._populate_carousel()

    def _populate_carousel(self):
        if self.carousel.slides:
            return
        for v in self.values:
            label = RoleLabel(
                text=v,
                color=self.font_color
            )
            label.bind(texture_size=self._adjust_carousel_size)
            self.bind(font_color=label.setter('color'))
            self.carousel.add_widget(label)

    def reset(self):
        self.carousel.index = 0

    def load_next(self):
        '''Patched to fix kivy bug
        '''
        if len(self.carousel.slides) > 1:
            w, h = self.carousel.size
            _direction = {
                'top': -h / 2,
                'bottom': h / 2,
                'left': w / 2,
                'right': -w / 2}
            _offset = _direction[self.carousel.direction]
            self.carousel._offset = _offset
            self.carousel._start_animation()


class RoleIcon(ToggleButtonGroupBehavior, ImageToggleButton):
    __events__ = ('on_disabled_click', )
    key = StringProperty()
    prefix = StringProperty()
    suffix = StringProperty()
    icon_set = StringProperty()
    bubble_selected = StringProperty()
    bubble = ListProperty([])
    _bubble = None

    def __init__(self, **kwargs):
        super(RoleIcon, self).__init__(**kwargs)

    def on_bubble(self, instance, value):
        if value:
            self.bubble_selected = value[0]

    def on_disabled_click(self):
        pass

    def _set_bubble_x(self, bubb, width):
        dist = post_roleicon_bubble_container_min_distance
        if (self.center_x - width/2) < (self.parent.x + dist):
            bubb.x = int(dist)
        elif (self.center_x + width/2) > (self.parent.right - dist):
            bubb.right = int(self.to_local(self.parent.width - dist, 0, relative=True)[0])
        else:
            bubb.center_x = int(self.width/2)

    def _bubble_text_changed(self, instance, value):
        self.bubble_selected = value

    def _move_completed(self, *args):
        super(RoleIcon, self)._move_completed(*args)
        if not self._bubble:
            self._bubble = RoleBubble(
                values=self.bubble,
                icon_set=self.icon_set,
                y=int(self.height+post_roleicon_bubble_bottom_spacing),
                opacity=0,
                arrow_x=int(self.width/2))
            self._bubble.bind(
                width=self._set_bubble_x,
                text=self._bubble_text_changed)
            self.bind(icon_set=self._bubble.setter('icon_set'))
        if self._bubble not in self.children:
            self.add_widget(self._bubble)
            Animation(opacity=1, d=.2).start(self._bubble)

    def on_state(self, instance, value):
        if not self.bubble:
            self.state == 'normal'
            return

        super(RoleIcon, self).on_state(instance, value)

        if self._bubble and self._bubble in self.children:
            if value == 'normal':
                self.remove_widget(self._bubble)
            if value == 'down':
                self._bubble.load_next()

    # def _trigger_hide_label(self, *args):
    #     super(RoleIcon, self)._trigger_hide_label(*args)
    #     self.remove_widget(self._bubble)

    def on_touch_down(self, touch):
        if self.disabled and self.collide_point(*touch.pos):
            self.dispatch('on_disabled_click')
            return True
        # we are disabled - don't make the switch
        if self.opacity < 0.9:
            return False

        return super(RoleIcon, self).on_touch_down(touch)


class PostScreen(InteractiveScreen):
    __events__ = ('on_close', 'on_post', 'on_post_created', 'on_post_failed')
    post_background = ObjectProperty()
    thumbs_container = ObjectProperty()
    themes_container = ObjectProperty()
    scrollview = ObjectProperty()
    post_textinput = ObjectProperty()
    write_post_icon = ObjectProperty()
    icon_set = StringProperty('light')

    current_theme = None
    current_role = None

    role_prefix = StringProperty('')
    role_suffix = StringProperty('')
    role_desc = StringProperty('')

    post_color = None
    post_image_key = None
    posted = False
    tutorial_shown = False

    def __init__(self, **kwargs):
        super(PostScreen, self).__init__(**kwargs)
        self.populate_themes()

    def on_close(self):
        pass

    def on_write_post_icon(self, instance, value):
        value.bind(on_touch_up=self._write_post_clicked)

    def _write_post_clicked(self, icon, touch):
        pt = self.post_textinput
        if icon.collide_point(*touch.pos) and not pt.focus:
            pt.focus = True
            return True

    def on_post_created(self, post_key):
        def _update(ds):
            ds.add(post_key)
        favorites_ds.update(_update)
        self.clear_inputs()
        self.post_textinput._refresh_hint_text()

    def clear_inputs(self):
        self.post_textinput.text = ''
        # self.current_theme = None
        self.current_role = None
        self.scrollview.scroll_x = 0
        self.scrollview.effect_x.value = 0 # fixes a bug in the scrollview
        self.post_background.color = get_color_from_hex('#212121')
        self.post_image_key = None
        if self.themes_container:
            for ti in self.themes_container.children[:]:
                ti.state = 'normal'
                if ti._bubble:
                    ti._bubble.reset()
        if self.thumbs_container:
            for ti in self.thumbs_container.children[:]:
                ti.state = 'normal'
            if len(self.thumbs_container.children)>1:
                self.thumbs_container.children[len(self.thumbs_container.children)-2].state = 'down'
        self.icon_set = 'light'
        self.write_post_icon.opacity = 1

    def on_post_failed(self, reason):
        Logger.error('PostScreen: post failed (%s)' % reason)

    def on_post(self):
        from modules.core.android_utils import Toast
        Toast('posting...')
        LogTestFairy('Post published')
        self.posted = True

        text = self.post_textinput.text.strip()
        if not text:
            return

        # so we don't double post
        self.post_textinput.text = ''

        if not PostsManager.streams:
            Logger.info('on_post: no channel to post to!')
            return
        chan_key = PostsManager.streams[0].key
        if self.post_color:
            background = 'color:%s' % self.post_color
        else:
            background = self.post_image_key

        def dispatch_created(key, **kwargs):
            Toast('posted successfully')
            self.dispatch('on_post_created', key)

        def dispatch_error(reason, *largs):
            Toast('posting failed')
            self.dispatch('on_post_failed', reason)

        post(
            content=text[:comment_length_limit],
            role="none",
            role_text="",
            theme=self.current_theme,
            background=background,
            channels=[chan_key],
            on_created=dispatch_created,
            on_error=dispatch_error)

    def on_enter(self, *args):
        LogTestFairy('Write Post')
        LogTestFairy('Write screen')

        self.populate_thumbs(DEFAULT_THEME)

    def on_pre_enter(self, *args):
        self.clear_inputs()
        self.post_textinput._refresh_hint_text()
        self.update_role_desc_linkedin()
        self._apply_to_theme_icons(lambda ti: ti.bind(state=self.theme_changed))

    def on_pre_leave(self, *args):
        if self.posted:
            LogTestFairy('Write Post exit')
        else:
            LogTestFairy('Write Post exit without publishing')

        self._apply_to_theme_icons(lambda ti: ti.unbind(state=self.theme_changed))
        if self.post_textinput.focus:
            self.post_textinput.focus = False

    def on_leave(self, *args):
        pass

    def on_icon_set(self, instance, value):
        def foo(ti):
            ti.icon_set = value
        self._apply_to_theme_icons(foo)

    def _update_role_desc(self, instance, value):
        # only update from a currently selected role
        if self.current_role == instance.key:
            self.role_desc = value

    def theme_changed(self, instance, value):
        if self.post_textinput:
            self.post_textinput.focus = False
        if value == 'down' and self.current_role != instance.key:
            self.current_role = instance.key
            self.role_prefix = format_vowel(instance.prefix, instance.bubble)
            self.role_suffix = instance.suffix
            if instance.bubble and len(instance.bubble) > 0:
                self.role_desc = instance.bubble[0]
            LogTestFairy('Write Post role changed to %s' % self.current_role)

    def set_color(self, theme, color):
        self.icon_set = theme.get_iconset_from_color(color)
        if self.icon_set:
            self.post_color = color
            self.post_background.color = get_color_from_hex(color)
            self.post_image_key = None

    def set_image_key(self, theme, image_key):
        self.icon_set = theme.get_iconset(image_key)
        if self.icon_set:
            self.post_image_key = image_key
            self.post_background.image = get_image_path(theme.key, image_key)
            self.post_background.color = []
            self.post_color = None

    def thumb_changed(self, instance, value):
        if value == 'down':
            t = get_post_theme(self.current_theme)
            if not t:
                return
            if isinstance(instance, BackgroundImage):
                LogTestFairy('Write Post image bkg pressed')
                self.set_image_key(t, instance.thumb_key)
            elif isinstance(instance, BackgroundColor):
                LogTestFairy('Write Post color bkg pressed')
                self.set_color(t, instance.color)

    def _apply_to_theme_icons(self, func):
        if self.themes_container:
            for ti in self.themes_container.children[:]:
                func(ti)

    def update_role_desc_linkedin(self, dlg=None):
        for c in self.themes_container.children:
            # test if we have several options
            text = get_linkedin_data(c.key+'_options')
            if not text:
                text = [get_linkedin_data(c.key)]

            if len(text) == 1 and text[0] == '':
                text = []

            c.bubble = text
            if (type(text) is str and text == 'unknown') or\
                (type(text) is list and len(text)>0 and text[0] == 'unknown'):
                c.opacity = 0.5
            else:
                c.opacity = 1

            if dlg and dlg.userdata == c.key:
                c.trigger_action()

    def populate_themes(self, *args):
        c = self.themes_container
        if not c:
            self.bind(themes_container=self.populate_themes)
            return
        self.unbind(themes_container=self.populate_themes)

    def _add_thumb(self, theme_key, thumb_key, height):
        bi = BackgroundImage(
            height=height,
            thumb_key=thumb_key,
            allow_stretch=True,
            source=get_thumb_path(theme_key, thumb_key))
        bi.bind(state=self.thumb_changed)
        self.thumbs_container.add_widget(bi)

    def _add_color(self, color, height):
        bc = BackgroundColor(
            height=height,
            color=color)
        bc.bind(state=self.thumb_changed)
        self.thumbs_container.add_widget(bc)

    def _select_initial_thumb(self, *args):
        c = self.thumbs_container
        if c and c.children:
            c.children[-2].state = 'down'

    def populate_thumbs(self, theme_key, *args):
        c = self.thumbs_container
        if not c or c.height <= 0:
            self.bind(thumbs_container=partial(self.populate_thumbs, theme_key=theme_key))
            return
        if theme_key != self.current_theme:
            theme = get_post_theme(theme_key)
            thumbs = theme.thumbs
            # really sorting here?
            colors = sorted(theme.colors.keys())
            if len(colors) < len(thumbs):
                missing = len(thumbs) - len(colors)
                colors.extend([colors[-1]] * missing)
            Clock.unschedule(self._select_initial_thumb)
            c.clear_widgets()
            w = (c.height - (c.spacing[1] + c.padding[1] + c.padding[3])) / 2
            h = w
            total = len(thumbs)
            num_colors = len(colors)
            for i in range(0, int(total/2)):
                self._add_thumb(theme_key, thumbs[i*2 + 0], h)
                self._add_color(colors[(i*2 + 0) % num_colors], h)
                self._add_color(colors[(i*2 + 1) % num_colors], h)
                self._add_thumb(theme_key, thumbs[i*2 + 1], h)
            if total % 2 != 0:
                self._add_thumb(theme_key, thumbs[total-1], h)
                self._add_color(colors[(total-1) % num_colors], h)
            self.current_theme = theme_key

        Clock.schedule_once(self._select_initial_thumb, .1)

    def do_exit_input(self):
        if self.post_textinput.focus:
            self.post_textinput.focus = False
            return True
