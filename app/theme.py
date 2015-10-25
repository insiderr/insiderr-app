from kivy.utils import get_color_from_hex


def get_theme_atlas():
    theme_key = _resolve_theme_key()
    return 'atlas://data/themes/%dpx/screens/' % int(theme_key)

def get_post_atlas():
    theme_key = _resolve_theme_key()
    return 'atlas://data/themes/%dpx/themes/' % int(theme_key)

def _scale_to_theme_dpi(value):
    # make sure we have a dpi value
    _resolve_theme_key()
    if isinstance(value, list):
        return list(_scale_to_theme_dpi(v) for v in value)
    return int(value*_dpi_factor+0.5)

_dpi_factor = 1.
_theme_width = -1
_theme_height = -1
_theme_resource_width = -1
_theme_key = None
def _resolve_theme_key():
    global _theme_key
    if _theme_key:
        return _theme_key

    # find best matched theme size
    from kivy.core.window import Window
    # use non-rotated size
    ww, hh = Window.system_size
    print('WINDOW SIZE %s %s' % (ww, hh))
    global _dpi_factor
    global _theme_height
    global _theme_width
    global _theme_resource_width

    _theme_height = hh
    _theme_width = ww
    # should be more accurate to factor actual screen density
    _dpi_factor = float(ww)/720.0

    themes_widths = [1080, 768, 720, 640, 576, 540, 480, 400, 320]
    theme_distance = 999999
    _theme_key = None
    for ithemewidth in themes_widths:
        if theme_distance > abs(_theme_width-ithemewidth):
            _theme_resource_width = ithemewidth
            theme_distance = abs(_theme_width-ithemewidth)
            _theme_key = ithemewidth

    return _theme_key


#
# defines of theme sizes and fonts come here
#
anonymous_nick = 'Someone'

default_font_name = 'fonts/Alef-Regular.ttf'
default_font_size = _scale_to_theme_dpi(30)
back_color = get_color_from_hex('111111')
scroll_margins = _scale_to_theme_dpi([10, 10])

syspost_title_font_size = _scale_to_theme_dpi(42)
syspost_button_color = get_color_from_hex('01b8f2')
syspost_button_font = 'fonts/Lato-Light.ttf'

userpost_title_font_size = _scale_to_theme_dpi(42)
userpost_title_font = 'fonts/Lato-Regular.ttf'
userpost_font_color = {
    'dark': get_color_from_hex('000000'),
    'light': get_color_from_hex('FFFFFF'),
}
userpost_top_bar_margins = _scale_to_theme_dpi([20, 20])
userpost_bottom_bar_margins = _scale_to_theme_dpi([20, 25])
userpost_bottom_bar_font_name = 'fonts/Lato-Light.ttf'
userpost_bottom_bar_font_size = _scale_to_theme_dpi(28)
userpost_bottom_bar_font_padding = _scale_to_theme_dpi([0, 3])
userpost_bottom_bar_role_spacing = _scale_to_theme_dpi(10)
userpost_bottom_bar_role_font_size = _scale_to_theme_dpi(32)

feed_userpost_spacing = _scale_to_theme_dpi(10)
feed_themes_menu_font_name = 'fonts/Lato-Light.ttf'
feed_themes_menu_font_size = _scale_to_theme_dpi(36)
feed_themes_menu_item_padding = _scale_to_theme_dpi([0, 20, 0, 20])

comments_status_font_name = 'fonts/Lato-Regular.ttf'
comments_status_font_size = _scale_to_theme_dpi(36)
comments_status_vert_spacing = _scale_to_theme_dpi(16)

comments_vertical_spacing = _scale_to_theme_dpi(5)
comments_comment_top_padding = _scale_to_theme_dpi(20)
comments_comment_font_name = 'fonts/Lato-Regular.ttf'
comments_comment_font_size = _scale_to_theme_dpi(30)
comments_comment_font_color = get_color_from_hex('F4F5F5')
comments_comment_sections_spacing = _scale_to_theme_dpi(10)

comments_details_sections_spacing = _scale_to_theme_dpi(28)
comments_details_font_padding = _scale_to_theme_dpi([10, 3])
comments_details_font_name = 'fonts/Lato-Light.ttf'
comments_details_font_size = _scale_to_theme_dpi(28)
comments_details_font_color = get_color_from_hex('999999')
comments_role_font_color = get_color_from_hex('B9B9B9')

comments_comment_actions_spacing = _scale_to_theme_dpi(10)

comments_text_input_bar_min_height = _scale_to_theme_dpi(88)

comment_text_input_spacing = _scale_to_theme_dpi([10, 10])
comment_text_input_font_size = _scale_to_theme_dpi(36)
comment_text_input_hint_font_color = [.7, .7, .7, 1]
comment_text_input_cursor_color = [.5, .5, .5, 1]
#comment_text_input_back_color = get_color_from_hex('454545')
comment_text_input_back_color = get_color_from_hex('FFFFFF')
#comment_text_input_back_color_active = get_color_from_hex('D0D0D0')
comment_text_input_back_color_active = get_color_from_hex('FFFFFF')
comment_role_input_spacing = _scale_to_theme_dpi([50, 0])

post_themeicon_container_padding = _scale_to_theme_dpi([20, 0, 20, 20])
post_themeicon_container_item_extra_spacing = _scale_to_theme_dpi(8)
post_themeicon_font_name = 'fonts/Lato-Light.ttf'
post_themeicon_font_size = _scale_to_theme_dpi(22)
post_themeicon_font_color = {
    'dark': get_color_from_hex('333333'),
    'light': get_color_from_hex('CCCCCC'),
}

post_roletitle_font_size = _scale_to_theme_dpi(36)
post_roletitle_prefix_font_name = 'fonts/Lato-Regular.ttf'
post_roletitle_desc_font_name = 'fonts/Lato-Bold.ttf'
post_roletitle_desc_opacity = .8
post_roletitle_bottom_padding = _scale_to_theme_dpi(50)

post_roleicon_bubble_border = _scale_to_theme_dpi([12, 8, 12, 8])
post_roleicon_bubble_arrow_size = _scale_to_theme_dpi([9, 6])
post_roleicon_bubble_bottom_spacing = _scale_to_theme_dpi(20)
# min distance of bubble edge from container edge
post_roleicon_bubble_container_min_distance = _scale_to_theme_dpi(10)

favs_status_font_name = 'fonts/Lato-Regular.ttf'
favs_status_font_size = _scale_to_theme_dpi(36)

favs_menu_item_padding = _scale_to_theme_dpi([0, 20, 0, 20])
favs_menu_item_spacing = _scale_to_theme_dpi([10, 30])
favs_menu_item_font_name = 'fonts/Lato-Light.ttf'
favs_menu_item_font_size = _scale_to_theme_dpi(30)
favs_menu_border = _scale_to_theme_dpi(1)
favs_menu_back_color = get_color_from_hex('7f7f7f')

favs_userpost_height = _scale_to_theme_dpi(300)
favs_userpost_title_font_size = _scale_to_theme_dpi(35)

bar_margins = _scale_to_theme_dpi([20, 20])
bar_middle_label_color = get_color_from_hex('FFFFFF')
bar_middle_label_font_size = _scale_to_theme_dpi(32)
bar_middle_label_font_name = 'fonts/Lato-Bold.ttf'

popup_screen_opacity = .4

tutorial_dot_spacing = _scale_to_theme_dpi(20)
tutorial_progress_font_name = 'fonts/Lato-Light.ttf'
tutorial_progress_font_size = _scale_to_theme_dpi(25)
tutorial_bar_font_name = 'fonts/Lato-Regular.ttf'
tutorial_bar_font_size = _scale_to_theme_dpi(40)

share_menu_padding = _scale_to_theme_dpi([70, 50])
share_menu_spacing = _scale_to_theme_dpi([60, 30])
share_font_name = 'fonts/Lato-Light.ttf'
share_font_size = _scale_to_theme_dpi(28)

postitem_menu_padding = _scale_to_theme_dpi([10, 30, 10, 30])
postitem_menu_spacing = _scale_to_theme_dpi([10, 30])
postitem_font_name = 'fonts/Lato-Light.ttf'
postitem_font_size = _scale_to_theme_dpi(40)
postitem_border = _scale_to_theme_dpi(1)
postitem_back_color = get_color_from_hex('7f7f7f')

feedback_padding = _scale_to_theme_dpi([15, 15])
feedback_spacing = _scale_to_theme_dpi([0, 15])
feedback_font_name = 'fonts/Lato-Light.ttf'
feedback_font_size = _scale_to_theme_dpi(30)
feedback_button_padding = _scale_to_theme_dpi([20, 10])
feedback_button_font_name = 'fonts/Lato-Regular.ttf'
feedback_button_font_size = _scale_to_theme_dpi(28)

linkedin_title_font_size = _scale_to_theme_dpi(55)
linkedin_body_font_size = _scale_to_theme_dpi(30)
linkedin_bold_font_name = 'fonts/Lato-Bold.ttf'
linkedin_normal_font_name = 'fonts/Lato-Regular.ttf'
linkedin_spacing = _scale_to_theme_dpi([0, 20])
linkedin_padding = _scale_to_theme_dpi([37, 28, 37, 28])
linkedin_title_color = get_color_from_hex('555555ff')
linkedin_body_color = get_color_from_hex('888888ff')
linkedin_blue_color = get_color_from_hex('0097bdff')