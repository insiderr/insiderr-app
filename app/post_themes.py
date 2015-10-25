from kivy.logger import Logger
from config import post_themes
from utilities.unicode import convert_json_from_unicode
import json
from kivy.event import EventDispatcher
from kivy.properties import ListProperty, DictProperty, StringProperty


themes = []

class PostTheme(EventDispatcher):
    key = StringProperty()
    title = StringProperty()
    images = DictProperty()
    colors = DictProperty()
    thumbs = ListProperty()
    icons = ListProperty()
    icon_colors = ListProperty()

    icons_count = 0
    icon_colors_count = 0

    def get_icon_tuple(self, icon_index):
        if self.icons_count <= 0 or self.icon_colors_count <= 0:
            Logger.info('No icons or colors defined in this theme!')
            return None, None
        if icon_index == 0:
            # King (with first color)
            return self.icons[0], self.icon_colors[0]
        choices = (self.icons_count - 1) * self.icon_colors_count
        s = (icon_index % choices)
        return (
            self.icons[1 + (s % (self.icons_count - 1))],
            self.icon_colors[s / (self.icons_count - 1)])

    def on_icons(self, instance, value):
        if value:
            self.icons_count = max(0, len(value))

    def on_icon_colors(self, instance, value):
        if value:
            self.icon_colors_count = max(0, len(value))

    @staticmethod
    def get_color(background):
        if background.startswith('color:'):
            return background[len('color:'):]

    @staticmethod
    def get_background(background):
        if background.startswith('color:'):
            return ''
        return background

    def get_color_by_image(self, image_key):
        try:
            index = self.images.keys().index(image_key)
            if index is not None and self.colors:
                return (self.colors.keys()[index % len(self.colors.keys())])
        except Exception as e:
            pass

    def get_iconset_from_color(self, color):
        if color:
            return self.colors.get(color, None)

    def get_iconset(self, background):
        color = self.get_color(background)
        if color:
            return self.get_iconset_from_color(color)
        else:
            return self.images.get(background, None)


def get_image_path(post_theme_key, image_id):
    return 'data/post_themes/images/{}/{}.jpg'.format(post_theme_key, image_id)


def get_thumb_path(post_theme_key, thumb_id):
    return 'data/post_themes/thumbs/{}/{}.jpg'.format(post_theme_key, thumb_id)


def get_post_themes():
    global themes
    try:
        if not themes:
            with open(post_themes, 'r') as f:
                data = convert_json_from_unicode(
                    json.loads(f.read()))
                themes = [PostTheme(**pdata) for pdata in data]
    except Exception as ex:
        Logger.error('PostScreen: failed loading post themes: %s' % ex)
    return themes


def get_post_theme(theme_key):
    post_themes = get_post_themes()
    if post_themes:
        for t in post_themes:
            if t.key == theme_key:
                return t

        return post_themes[0]
