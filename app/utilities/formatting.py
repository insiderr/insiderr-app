from datetime import datetime
from time import strptime, mktime
from kivy.logger import Logger
from kivy.utils import get_color_from_hex as kivy_get_color_from_hex


def get_color_from_hex(color):
    if not color:
        return None
    if isinstance(color, list):
        return color
    return kivy_get_color_from_hex(color)


def get_formatted_when(time, absolute_time=False):
        try:
            if not absolute_time:
                d = datetime.now() - datetime.fromtimestamp(time)
                if d.total_seconds() < 60:
                    return 'just now'
                return format_time_diff(d)
            return datetime.fromtimestamp(time).strftime('%d-%b-%Y')
        except Exception:
            return ''


def format_time_diff(d):
    if d.days > 0:
        if d.days >= 365:
            y = d.days / 365
            return '%s year%s ago' % (y, 's' if y > 1 else '')
        elif d.days >= 30:
            m = d.days / 30
            return '%s month%s ago' % (m, 's' if m > 1 else '')
        return '%s day%s ago' % (d.days, 's' if d.days > 1 else '')
    elif d.seconds >= 3600:
        h = d.seconds / 3600
        return '%s hour%s ago' % (h, 's' if h > 1 else '')
    elif d.seconds >= 60:
        m = d.seconds / 60
        return '%s minute%s ago' % (m, 's' if m > 1 else '')
    return '%s second%s ago' % (d.seconds, 's' if d.seconds > 1 else '')


chars = ['', 'K', 'M']


def format_count(c, digits, char=''):
    if len(str(c)) + len(char) > digits:
        index = chars.index(char) + 1
        if index < len(chars):
            return format_count(c / 1000, digits, chars[index])
    return (c, char)


datetime_format = '%Y-%m-%dT%H:%M:%SZ'

def parse_timestring(time):
    try:
        return mktime(strptime(time, datetime_format))
    except:
        Logger.warning('parse_timestring(): incorrect time format %s' % time)
        return 0

def format_vowel(s, vowel_candidate):
    if vowel_candidate and vowel_candidate[0] in ('a', 'e', 'i', 'o', 'u'):
        return s.format(vowel='n')
    return s.format(vowel='')

