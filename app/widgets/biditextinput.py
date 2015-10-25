from kivy.uix.textinput import TextInput, _is_desktop, Cache_append, Cache_get
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.properties import AliasProperty, OptionProperty
from kivy.graphics import Color, Rectangle
from kivy.utils import boundary
from kivy import platform
from kivy.clock import Clock
from widgets.bidilabel import BidiCoreLabel
from modules.core.bidi.algorithm import get_display_hasrtl
from kivy.uix.textinput import FL_IS_NEWLINE
from kivy.base import EventLoop
import re
from kivy import __version__ as kivy_version
from kivy.logger import Logger


V = kivy_version.split('.')
# under v1.9.x
if int(V[0]) <= 1 and int(V[1]) < 9:
    # kivy 1.8 support
    class BidiTextInput(TextInput):
        delimiters = u' ,\'".;:\n\r\t'
        rtl_font = StringProperty('fonts/Alef-Regular.ttf')
        rtl_font_size = NumericProperty(-1)
        always_blink_cursor = BooleanProperty(False)
        rtl_halign_ignore = BooleanProperty(False)
        halign = OptionProperty('left', options=('left', 'right', 'center', 'justified'))
        valign = OptionProperty('bottom', options=('top', 'middle', 'bottom'))

        def _copy(self, data):
            self._ensure_clipboard()
            # on android leave unicode - otherwise it double encodes to utf-8
            if platform != 'android':
                data = data.encode(self._encoding) + b'\x00'
            from kivy.uix.textinput import Clipboard
            Clipboard.put(data, self._clip_mime_type)
            if data:
                self.cancel_selection()
                self._hide_cut_copy_paste(self._win)

        def __init__(self, **kwargs):
            # private
            self.last_line_rtl = False
            self.last_line_rtl_font = False
            self.last_ltr_font = ''
            self.topy = 0
            super(BidiTextInput, self).__init__(**kwargs)

        def on_text(self, *args):
            #self._refresh_hint_text()
            pass

        # Added support for valign features
        def _update_graphics(self, *largs):
            # Update all the graphics according to the current internal values.
            #
            # This is a little bit complex, cause we have to :
            #     - handle scroll_x
            #     - handle padding
            #     - create rectangle for the lines matching the viewport
            #     - crop the texture coordinates to match the viewport
            #
            # This is the first step of graphics, the second is the selection.

            self.canvas.clear()
            add = self.canvas.add

            lh = self.line_height
            dy = lh + self.line_spacing

            # adjust view if the cursor is going outside the bounds
            sx = self.scroll_x
            sy = self.scroll_y

            # draw labels
            if not self.focus and (not self._lines or (
                    not self._lines[0] and len(self._lines) == 1)):
                rects = self._hint_text_rects
                labels = self._hint_text_labels
                lines = self._hint_text_lines
            else:
                rects = self._lines_rects
                labels = self._lines_labels
                lines = self._lines
            padding_left, padding_top, padding_right, padding_bottom = self.padding
            x = self.x + padding_left
            y = self.top - padding_top + sy
            miny = self.y + padding_bottom
            maxy = self.top - padding_top
            self.topy = self.top - padding_top
            if self.valign[0]=='m':
                th = dy*len(labels) - self.line_spacing
                if th < maxy-miny :
                    y = self.top - padding_top - max(0, ((self.top-padding_top) - (self.y+padding_bottom) - th)/2)
                    self.topy = y
                    sy = self.scroll_y = 0
            elif self.valign[0]=='b':
                th = dy*len(labels) - self.line_spacing
                if th < maxy-miny :
                    y = self.top - padding_top - max(0, ((self.top-padding_top) - (self.y+padding_bottom) - th))
                    self.topy = y
                    sy = self.scroll_y = 0

            for line_num, value in enumerate(lines):
                if miny <= y <= maxy + dy:
                    texture = labels[line_num]
                    if not texture:
                        y -= dy
                        continue
                    size = list(texture.size)
                    texc = texture.tex_coords[:]

                    # calcul coordinate
                    viewport_pos = sx, 0
                    vw = self.width - padding_left - padding_right
                    vh = self.height - padding_top - padding_bottom
                    tw, th = list(map(float, size))
                    oh, ow = tch, tcw = texc[1:3]
                    tcx, tcy = 0, 0

                    # adjust size/texcoord according to viewport
                    if vw < tw:
                        tcw = (vw / tw) * tcw
                        size[0] = vw
                    if vh < th:
                        tch = (vh / th) * tch
                        size[1] = vh
                    if viewport_pos:
                        tcx, tcy = viewport_pos
                        tcx = tcx / tw * (ow)
                        tcy = tcy / th * oh

                    # cropping
                    mlh = lh
                    if y > maxy:
                        vh = (maxy - y + lh)
                        tch = (vh / float(lh)) * oh
                        tcy = oh - tch
                        size[1] = vh
                    if y - lh < miny:
                        diff = miny - (y - lh)
                        y += diff
                        vh = lh - diff
                        tch = (vh / float(lh)) * oh
                        size[1] = vh

                    texc = (
                        tcx,
                        tcy + tch,
                        tcx + tcw,
                        tcy + tch,
                        tcx + tcw,
                        tcy,
                        tcx,
                        tcy)

                    # add rectangle.
                    r = rects[line_num]
                    r.pos = int(x), int(y - mlh)
                    r.size = size
                    r.texture = texture
                    r.tex_coords = texc
                    add(r)

                y -= dy

            self._update_graphics_selection()

        # fix KIVY BUG with min height and padding
        # they mistakenly take the right padding instead of the bottom
        def _get_min_height(self):
            return (len(self._lines) * (self.line_height + self.line_spacing)
                    + self.padding[0] + self.padding[3])
        minimum_height = AliasProperty(_get_min_height, None,
                                       bind=('_lines', 'line_spacing', 'padding',
                                             'font_size', 'font_name', 'password',
                                             'hint_text'))

        # fix KIVY BUG when updating focus hint is not refreshed.
        def on_focus(self, instance, value, *largs):
            self._set_window(*largs)

            if value:
                if self.keyboard_mode != 'managed':
                    self._bind_keyboard()
            else:
                if self.keyboard_mode != 'managed':
                    self._unbind_keyboard()

            self._refresh_hint_text()

        def _bind_keyboard(self):
            self._set_window()
            win = self._win
            self._editable = editable = (not (self.readonly or self.disabled) or
                                         _is_desktop and
                                         self._keyboard_mode == 'system')

            if not _is_desktop and not editable:
                return

            keyboard = win.request_keyboard(
                self._keyboard_released, self, input_type=self.input_type)
            self._keyboard = keyboard
            if editable:
                keyboard.bind(
                    on_key_down=self._keyboard_on_key_down,
                    on_key_up=self._keyboard_on_key_up)
                if not self.always_blink_cursor:
                    Clock.schedule_interval(self._do_blink_cursor, 1 / 2.)
            else:
                # in non-editable mode, we still want shortcut (as copy)
                keyboard.bind(
                    on_key_down=self._keyboard_on_key_down)

        def on_always_blink_cursor(self, instance, value):
            if value:
                Clock.schedule_interval(self._do_blink_cursor, 1 / 2.)
            elif not self.focus:
                Clock.unschedule(self._do_blink_cursor)

        def _unbind_keyboard(self):
            Clock.schedule_interval(self._do_blink_cursor, 1 / 2.)
            self._cursor_blink_time = Clock.get_time()
            self._set_window()
            win = self._win
            if self._keyboard:
                keyboard = self._keyboard
                keyboard.unbind(
                    on_key_down=self._keyboard_on_key_down,
                    on_key_up=self._keyboard_on_key_up)
                keyboard.release()
                self._keyboard = None

            self.cancel_selection()
            if not self.always_blink_cursor:
                Clock.unschedule(self._do_blink_cursor)
            self._hide_cut_copy_paste(win)
            self._hide_handles(win)
            self._win = None

        def _keyboard_on_key_down(self, window, keycode, text, modifiers):
            # hexa = ''
            # for i in range(len(text)) :
            #     hexa = hexa+( '%02x,' % ord(text[i]) )
            # Logger.info('BidiTextInput: [%s] [%s]==<%s> [%s]' % (keycode,text, hexa, modifiers))
            if platform == 'android':
                # this is a bit hackish but it ignores android special softkeyboard
                # strokes.
                if (keycode[0] == 32) and (len(text) == 0) and (not modifiers):
                    return
                if (keycode[0] == 113) and (len(text) == 1) and (ord(text[0]) == 04) and (not modifiers):
                    return
            super(BidiTextInput, self)._keyboard_on_key_down(
                window, keycode, text, modifiers)

        def _get_text_width(self, text, tab_width, _label_cached):
            # Return the width of a text, according to the current line options
            kw = self._get_line_options()
            try:
                cid = u'{}\0{}'.format(text, kw)
            except UnicodeDecodeError:
                cid = '{}\0{}'.format(text, kw)

            width = Cache_get('textinput.width', cid)
            if width:
                return width
            if not _label_cached:
                _label_cached = self._label_cached
            text = text.replace('\t', ' ' * tab_width)

            if not self.password:
                width = _label_cached.get_extents(text)[0]
            else:
                width = _label_cached.get_extents('*' * len(text))[0]

            Cache_append('textinput.width', cid, width)
            return width

        def cursor_offset(self):
            offset = super(BidiTextInput, self).cursor_offset()
            viewport_width = self.width - self.padding[0] - self.padding[2]
            if self.halign in ['center'] and self._lines:
                row = min(len(self._lines)-1, self.cursor_row)
                text_width = self._get_text_width(self._lines[row], self.tab_width, self._label_cached)
                if self.last_line_rtl:
                    offset = viewport_width - int((viewport_width - text_width)/2) - offset
                else:
                    offset = offset + int((viewport_width - text_width) / 2)
            else:
                if self.last_line_rtl:
                    offset = viewport_width - offset
            return offset

        def _draw_selection(self, *largs):
            pos, size, line_num, (s1c, s1r), (s2c, s2r),\
                _lines, _get_text_width, tab_width, _label_cached, width,\
                padding_left, padding_right, x, canvas_add, selection_color = largs
            # Draw the current selection on the widget.
            if line_num < s1r or line_num > s2r:
                return
            x, y = pos
            w, h = size
            x1 = x
            x2 = x + w
            if line_num == s1r:
                lines = _lines[line_num]
                x1 -= self.scroll_x
                x1 += _get_text_width(lines[:s1c], tab_width, _label_cached)
            if line_num == s2r:
                lines = _lines[line_num]
                x2 = (x - self.scroll_x) + _get_text_width(lines[:s2c],
                                                           tab_width,
                                                           _label_cached)

            if self._lines:
                row = min(len(self._lines)-1, line_num)
                text_width = self._get_text_width(self._lines[row], self.tab_width, self._label_cached)
                width_minus_padding = text_width
            else:
                width_minus_padding = width - (padding_right + padding_left)
            maxx = x + width_minus_padding
            if not self.last_line_rtl:
                if x1 > maxx:
                    return
                x1 = max(x1, x)
                x2 = min(x2, x + width_minus_padding)
                dx21 = x2 - x1
                if self.halign in ['center'] and self._lines:
                    viewport_width = self.width - self.padding[0] - self.padding[2]
                    x1 += int((viewport_width - text_width) / 2)
            else:
                #Logger.info('BidiTextInput: _draw_selection %d %d %d %d' %(x,x1,x2,maxx))
                x1 = max(x1, x)
                x2 = min(x2, x + width_minus_padding)
                dx21 = x2 - x1
                x1 = self.x + self.width - \
                    self.padding[2] - (x2 - (self.x + self.padding[0]))
                if self.halign in ['center'] and self._lines:
                    viewport_width = self.width - self.padding[0] - self.padding[2]
                    row = min(len(self._lines)-1, line_num)
                    text_width = self._get_text_width(self._lines[row], self.tab_width, self._label_cached)
                    dx21 = min(dx21, text_width)
                    x1 -= int((viewport_width - text_width) / 2)

            canvas_add(Color(*selection_color, group='selection'))
            canvas_add(Rectangle(
                pos=(x1, pos[1]), size=(dx21, size[1]), group='selection'))

        def get_cursor_from_xy(self, x, y):
            #Logger.info('BidiTextInput: get_cursor_from_xy')

            if self.last_line_rtl:
                #Logger.info('BidiTextInput: get_cursor_from_xy %d %d' % (x,y))
                # mirror to the left side
                x = self.x + self.width - \
                    self.padding[2] - (x - (self.x + self.padding[0]))

            padding_top = self.padding[1]
            l = self._lines
            dy = self.line_height + self.line_spacing
            cx = x - self.x
            scrl_y = self.scroll_y
            scrl_x = self.scroll_x
            scrl_y = scrl_y / dy if scrl_y > 0 else 0
            cy = (self.topy + scrl_y * dy) - y
            cy = int(boundary(round(cy / dy - 0.5), 0, len(l) - 1))
            dcx = 0
            _get_text_width = self._get_text_width
            _tab_width = self.tab_width
            _label_cached = self._label_cached

            if self.halign in ['center'] and self._lines:
                    text_width = self._get_text_width(self._lines[cy], self.tab_width, self._label_cached)
                    viewport_width = self.width - self.padding[0] - self.padding[2]
                    cx -= int((viewport_width - text_width) / 2)

            if not self.last_line_rtl:
                for i in range(1, len(l[cy]) + 1):
                    if _get_text_width(l[cy][:i],
                                       _tab_width,
                                       _label_cached) >= cx + scrl_x:
                        break
                    dcx = i
            else:
                for i in range(1, len(l[cy]) + 1):
                    if _get_text_width(l[cy][:i],
                                       _tab_width,
                                       _label_cached) >= cx + scrl_x:
                        break
                    dcx += 1

            cx = dcx
            return cx, cy

        def _get_line_options(self):
            ##options = super(BidiTextInput, self)._get_line_options()
            # Get or create line options, to be used for Label creation
            _label_cached_create = False
            if self._line_options is None:
                _label_cached_create = True
                self._line_options = {
                    'font_size': self.font_size,
                    'font_name': self.font_name,
                    'anchor_x': 'left',
                    'anchor_y': 'top',
                    'padding_x': 0,
                    'padding_y': 0,
                    'padding': (0, 0)}
            options = self._line_options

            #Logger.info('BidiTextInput: _get_line_options, rtl=%s,%s: %s' % (self.last_line_rtl,self.last_line_rtl_font,options))
            options['halign'] = self.halign
            if self.last_line_rtl:
                if self.last_ltr_font == '':
                    self.last_ltr_font = self.font_name
                if self.rtl_font:
                    options['font_name'] = self.rtl_font
                    # update us - for cursor position
                    self.font_name = self.rtl_font
                    if self.rtl_font_size > 0:
                        options['font_size'] = self.rtl_font_size
                if (self.halign != 'center') and (self.halign != 'justified'):
                    options['halign'] = 'right'
                options['padding_x'] = 0
                options['padding'] = [0, options['padding_y']]
                # in order to avoid miss alignment between input object and corelabel
                # (they break line and we dont, give it extra 1px width)
                options['text_size'] = [self.width
                                        -self.padding[0] -self.padding[2], options.get('text_size', [None, None])[1]]

                # don't let the label do the line breaking, we are responsible fo it
                options['force_single_line'] = True

                options['anchor_x'] = 'right'
                options['rtl'] = True
            else:
                if self.last_line_rtl_font:
                    if self.last_ltr_font == '':
                        self.last_ltr_font = self.font_name
                    if self.rtl_font:
                        options['font_name'] = self.rtl_font
                        self.font_name = self.rtl_font
                        if self.rtl_font_size > 0:
                            options['font_size'] = self.rtl_font_size

                elif self.last_ltr_font != '':

                    options['font_name'] = self.last_ltr_font

                    # update us back - for cursor position
                    self.font_name = self.last_ltr_font

                    self.last_ltr_font = ''

                options['rtl'] = False

                # don't let teh label do the line breaking, we are responsible fo it
                options['force_single_line'] = True

                if (self.halign != 'center') and (self.halign != 'justified'):
                    options['halign'] = 'left'
                    options['text_size'] = [None, None]
                else:
                    # in order to avoid miss alignment between input object and corelabel
                    # (they break line and we dont, give it extra 1px width)
                    options['text_size'] = [self.width
                                            -self.padding[0] -self.padding[2], None]

            if _label_cached_create:
                self._label_cached = BidiCoreLabel(**options)

            ##Logger.info('OPTIONSSSS %s' % options)
            self._line_options = options
            return options

        def _create_line_label_super(self, text, hint=False):
            # Create a label from a text, using line options
            ntext = text.replace(u'\n', u'').replace(u'\t', u' ' * self.tab_width)
            if self.password and not hint:  # Don't replace hint_text with *
                ntext = u'*' * len(ntext)
            kw = self._get_line_options()
            cid = '%s\0%s' % (ntext, str(kw))
            texture = Cache_get('textinput.label', cid)

            if not texture:
                # FIXME right now, we can't render very long line...
                # if we move on "VBO" version as fallback, we won't need to
                # do this.  try to found the maximum text we can handle
                label = None
                label_len = len(ntext)
                ld = None
                while True:
                    try:
                        rtext = ntext[:label_len]
                        label = BidiCoreLabel(text=rtext, **kw)
                        label.refresh()
                        if ld is not None and ld > 2:
                            ld = int(ld / 2)
                            label_len += ld
                        else:
                            break
                    except:
                        # exception happen when we tried to render the text
                        # reduce it...
                        if not ld:
                            ld = len(ntext)
                        if ld == 0:
                            break
                        ld = int(ld / 2)
                        if ld < 2 and label_len:
                            label_len -= 1
                        label_len -= ld
                        continue

                # ok, we found it.
                texture = label.texture
                Cache_append('textinput.label', cid, texture)
            return texture


        def _update_last_line_rtl(self, text):
            # check bidi font and direction
            base_level, has_rtl = get_display_hasrtl(text)
            right_to_left = (base_level != 0)

            #Logger.info('BidiTextInput: rtl=%s %s %s: [%s] [%s]' % (right_to_left,base_level,has_rtl,text,rtext))
            self.last_line_rtl = right_to_left or self.last_line_rtl
            self.last_line_rtl_font = (self.last_line_rtl) or has_rtl

            # ignore left to right direction
            if self.rtl_halign_ignore:
                self.last_line_rtl = False

        def _set_line_text(self, line_num, text):
            prev_rtl = self.last_line_rtl
            self._update_last_line_rtl(text)
            if prev_rtl != self.last_line_rtl:
                # trigger update on text - we changed the rtl flag
                self._trigger_refresh_text()

            super(BidiTextInput, self)._set_line_text(line_num, text)

        def _refresh_text(self, text, *largs):
            self._update_last_line_rtl(text)
            super(BidiTextInput, self)._refresh_text(text, *largs)

        def _create_line_label(self, text, hint=False):
            # don't process hint_text when not needed
            if hint and not (not self._lines or (not self._lines[0] and len(self._lines) == 1)):
                return

            return self._create_line_label_super(text, hint)

        def _get_cursor(self):
            return self._cursor

        def _set_cursor(self, pos):
            if not self.last_line_rtl:
                padding_left = self.padding[0]
                padding_right = self.padding[2]
                viewport_width = self.width - padding_left - padding_right ##self.font_size*1
                sx = self.scroll_x
                _set_cursor_success = super(BidiTextInput, self)._set_cursor(pos)
                offset = self.cursor_offset()
                if _set_cursor_success is True:
                    if self.last_line_rtl_font:
                        if sx == 0:
                            self.scroll_x = 0
                    else:
                        if offset >= viewport_width + sx:
                            self.scroll_x = offset - viewport_width
                        elif offset >= viewport_width and ((offset-sx) % viewport_width < self.font_size):
                            self.scroll_x = offset - viewport_width
                        elif ((offset-sx) % viewport_width < self.font_size):
                            self.scroll_x = 0
                        elif offset < sx:
                            self.scroll_x = offset
                    return True
                return

            if not self._lines:
                self._trigger_refresh_text()
                return
            l = self._lines
            cr = boundary(pos[1], 0, len(l) - 1)
            cc = boundary(pos[0], 0, len(l[cr]))
            cursor = cc, cr
            if self._cursor == cursor:
                return

            self._cursor = cursor

            # adjust scrollview to ensure that the cursor will be always inside our
            # viewport.
            padding_left = self.padding[0]
            padding_right = self.padding[2]
            viewport_width = self.width - padding_left - padding_right
            sx = self.scroll_x
            offset = self.cursor_offset()

            # if offset is outside the current bounds, reajust
            # reverse offset so reverse scroll...
            scroll_x = sx
            if offset > viewport_width + sx:
                scroll_x = offset
            elif offset < 0:
                scroll_x = 0 #offset
            elif offset < sx:
                scroll_x = offset - viewport_width

            # do the same for Y
            # this algo try to center the cursor as much as possible
            dy = self.line_height + self.line_spacing
            offsety = cr * dy
            sy = self.scroll_y
            padding_top = self.padding[1]
            padding_bottom = self.padding[3]
            viewport_height = self.height - padding_top - padding_bottom - dy
            if offsety > viewport_height + sy:
                sy = offsety - viewport_height
            if offsety < sy:
                sy = offsety

            # update only now - since this function is actually already bounded to the scroll property
            self.scroll_y = sy
            self.scroll_x = scroll_x

            return True

        cursor = AliasProperty(_get_cursor, _set_cursor)

        def _get_cursor_pos(self):
            # if not self.last_line_rtl:
            #     return super(BidiTextInput, self)._get_cursor_pos()

            # return the current cursor x/y from the row/col
            dy = self.line_height + self.line_spacing
            padding_left = self.padding[0]
            padding_top = self.padding[1]
            left = self.x + padding_left

            #
            padding_left, padding_top, padding_right, padding_bottom = self.padding
            sy = self.scroll_y
            miny = self.y + padding_bottom
            maxy = self.top - padding_top

            # recalc topy
            top = self.top - padding_top
            if self.valign[0]=='m':
                th = dy*len(self._lines_labels) - self.line_spacing
                if th < maxy-miny :
                    y = self.top - padding_top - max(0, ((self.top-padding_top) - (self.y+padding_bottom) - th)/2)
                    top = y
            elif self.valign[0]=='b':
                th = dy*len(self._lines_labels) - self.line_spacing
                if th < maxy-miny :
                    y = self.top - padding_top - max(0, ((self.top-padding_top) - (self.y+padding_bottom) - th))
                    top = y

            #top = self.topy
            y = top + self.scroll_y
            y -= self.cursor_row * dy
            x, y = left + self.cursor_offset() - self.scroll_x, y
            if x < left:
                self.scroll_x = 0
                x = left
            if y > top:
                y = top
                self.scroll_y = 0
            return x, y
        cursor_pos = AliasProperty(_get_cursor_pos, None, bind=(
            'cursor', 'padding', 'pos', 'size', 'focus','_lines',
            'scroll_x', 'scroll_y'))

        # fix KIVY BUG
        # new line check with self.width-padding instead of just self.width
        def insert_text(self, substring, from_undo=False):
            '''Insert new text at the current cursor position. Override this
            function in order to pre-process text for input validation.
            '''
            if self.readonly or not substring:
                return

            self._hide_handles(self._win)

            # check for command modes
            if ord(substring[0]) == 1:
                self._command_mode = True
                self._command = ''
            if ord(substring[0]) == 2:
                self._command_mode = False
                self._command = self._command[1:]

            if self._command_mode:
                self._command += substring
                return

            _command = self._command
            if _command and ord(substring[0]) == 2:
                from_undo = True
                # the first occurrence of ":" splits the string into command/data
                spliter = _command.find(':')
                if spliter < 0:
                    self._command = ''
                    return
                data = _command[spliter+1:]
                _command = _command[:spliter]
                self._command = ''
                if _command == 'DEL':
                    count = int(data)
                    end = self.cursor_index()
                    self._selection_from = max(end - count, 0)
                    self._selection_to = end
                    self._selection = True
                    self.delete_selection(from_undo=True)
                    return
                elif _command == 'INSERT':
                    substring = data
                elif _command == 'INSERTN':
                    from_undo = False
                    substring = data

            if not from_undo and self.multiline and self.auto_indent \
                    and substring == u'\n':
                substring = self._auto_indent(substring)

            cc, cr = self.cursor
            sci = self.cursor_index
            ci = sci()
            text = self._lines[cr]
            len_str = len(substring)
            new_text = text[:cc] + substring + text[cc:]
            self._set_line_text(cr, new_text)

            wrap = (self._get_text_width(
                new_text,
                self.tab_width,
                self._label_cached) >= self.width - self.padding[0] - self.padding[2] )
            if len_str > 1 or substring == u'\n' or wrap:
                # Avoid refreshing text on every keystroke.
                # Allows for faster typing of text when the amount of text in
                # TextInput gets large.

                start, finish, lines,\
                    lineflags, len_lines = self._get_line_from_cursor(cr, new_text)
                # calling trigger here could lead to wrong cursor positioning
                # and repeating of text when keys are added rapidly in a automated
                # fashion. From Android Keyboard for example.
                self._refresh_text_from_property('insert', start, finish, lines,
                                                 lineflags, len_lines)

            self.cursor = self.get_cursor_from_index(ci + len_str)
            # handle undo and redo
            self._set_unredo_insert(ci, ci + len_str, substring, from_undo)

        # kivy bug, we need to refresh all lines if we have multilines
        def do_backspace(self, from_undo=False, mode='bkspc'):
            '''Do backspace operation from the current cursor position.
            This action might do several things:

                - removing the current selection if available.
                - removing the previous char and move the cursor back.
                - do nothing, if we are at the start.

            '''
            if self.readonly:
                return
            cc, cr = self.cursor
            _lines = self._lines
            text = _lines[cr]
            cursor_index = self.cursor_index()
            text_last_line = _lines[cr - 1]

            if cc == 0 and cr == 0:
                return
            _lines_flags = self._lines_flags
            start = cr
            if cc == 0:
                substring = u'\n' if _lines_flags[cr] else u' '
                new_text = text_last_line + text
                self._set_line_text(cr - 1, new_text)
                self._delete_line(cr)
                start = cr - 1
            else:
                #ch = text[cc-1]
                substring = text[cc - 1]
                new_text = text[:cc - 1] + text[cc:]
                self._set_line_text(cr, new_text)

            # refresh just the current line instead of the whole text
            start, finish, lines, lineflags, len_lines =\
                self._get_line_from_cursor(start, new_text)
            # avoid trigger refresh, leads to issue with
            # keys/text send rapidly through code.
            self._refresh_text_from_property('del', start, finish, lines,
                                             lineflags, len_lines)

            self.cursor = self.get_cursor_from_index(cursor_index - 1)
            # handle undo and redo
            self._set_undo_redo_bkspc(
                cursor_index,
                cursor_index - 1,
                substring, from_undo)

        # adjust specifically with value
        def _tokenize(self, text):
            # Tokenize a text string from some delimiters
            if text is None:
                return
            delimiters = self.delimiters # u' ,\'".;:\n\r\t'
            oldindex = 0
            for index, char in enumerate(text):
                if char not in delimiters:
                    continue
                if oldindex != index:
                    yield text[oldindex:index]
                yield text[index:index + 1]
                oldindex = index + 1
            yield text[oldindex:]

        # Bug in Kivy split line, if the word is longer than the max width,
        # we need to split the word anyhow
        def _split_smart(self, text):
            # Do a "smart" split. If autowidth or autosize is set,
            # we are not doing smart split, just a split on line break.
            # Otherwise, we are trying to split as soon as possible, to prevent
            # overflow on the widget.

            padding_left = self.padding[0]
            padding_right = self.padding[2]
            width = self.width - padding_left - padding_right

            # depend of the options, split the text on line, or word
            if not self.multiline or width <= 0:
                lines = text.split(u'\n')
                lines_flags = [0] + [FL_IS_NEWLINE] * (len(lines) - 1)
                return lines, lines_flags

            # no autosize, do wordwrap.
            x = flags = 0
            line = []
            lines = []
            lines_flags = []
            _join = u''.join
            lines_append, lines_flags_append = lines.append, lines_flags.append
            text_width = self._get_text_width
            _tab_width, _label_cached = self.tab_width, self._label_cached

            # try to add each word on current line.
            for word in self._tokenize(text):
                #if word==u'':
                #    continue
                is_newline = (word == u'\n')
                w = text_width(word, _tab_width, _label_cached)
                # if we have more than the width, or if it's a newline,
                # push the current line, and create a new one
                if (x + w > width) or is_newline:
                    # now we check if we already started a new line and
                    # the word is still to big
                    if x==0 or w>width:
                        # if the word is too long commit the current and start a new one
                        if w>width and line:
                            lines_append(_join(line))
                            lines_flags_append(flags)
                            flags = 0
                            line = []
                            x = 0
                        # try to find the max chars that fits in the line
                        newword = word
                        wordfound = True
                        while len(newword)>0 and wordfound:
                            wordfound = False
                            for i in range(0,len(newword)):
                                word = newword[0:len(newword)-i]
                                w = text_width(word, _tab_width, _label_cached)
                                if x + w <= width:
                                    newword = newword[len(newword)-i:]
                                    wordfound = True
                                    if newword:
                                        lines_append(_join(word))
                                        lines_flags_append(flags)
                                        flags = 0
                                        line = []
                                        x = 0
                                    break
                    elif line:
                        lines_append(_join(line))
                        lines_flags_append(flags)
                        flags = 0
                        line = []
                        x = 0
                    else:
                        x += w
                        line.append(word)
                if is_newline:
                    flags |= FL_IS_NEWLINE
                else:
                    x += w
                    line.append(word)
            if line or flags & FL_IS_NEWLINE:
                lines_append(_join(line))
                lines_flags_append(flags)

            #if not lines:
            #    lines = [u'']
            return lines, lines_flags

        # they have some bugs in their code,
        # we just protect against exceptions here
        def _show_cut_copy_paste(self, pos, win, parent_changed=False, mode='', *l):
            try:
                # position should always be above selectors
                s1c, s1r = self.get_cursor_from_index(self._selection_to)
                s2c, s2r = self.get_cursor_from_index(self._selection_from)
                c,r = (s1c, s1r) if s1r<s2r else (s2c, s2r)
                pos = ( int(self.cursor_pos[0]),
                        int(self._lines_rects[r].pos[1] + self._lines_rects[r].size[1]/2) )
                super(BidiTextInput, self)._show_cut_copy_paste(
                    pos, win, parent_changed, mode, *l)
            except Exception:
                pass
            return

        def delete_selection(self, from_undo=False):
            super(BidiTextInput, self).delete_selection(from_undo)
            self._hide_cut_copy_paste(self._win)

        def _show_handles(self, win):
            try:
                super(BidiTextInput, self)._show_handles(win)
            except Exception:
                pass
            return

        def _hide_cut_copy_paste(self, win=None):
            try:
                super(BidiTextInput, self)._hide_cut_copy_paste(win)
            except Exception:
                pass
            return

        def _hide_handles(self, win=None):
            try:
                super(BidiTextInput, self)._hide_handles(win)
            except Exception:
                pass
            return

        def _position_handles(self, mode='both'):
            try:
                super(BidiTextInput, self)._position_handles(mode)
            except Exception:
                pass
            return

        def _handle_move(self, instance, touch):
            try:
                super(BidiTextInput, self)._handle_move(instance, touch)
            except Exception:
                pass
            return

        def _handle_released(self, instance):
            try:
                super(BidiTextInput, self)._handle_released(instance)
            except Exception:
                pass
            return

        def _handle_pressed(self, instance):
            try:
                super(BidiTextInput, self)._handle_pressed(instance)
            except Exception:
                pass
            return

        def on_double_tap(self):
            try:
                super(BidiTextInput, self).on_double_tap()
                Clock.schedule_once(lambda dt: self._show_cut_copy_paste((0,0), self._win))
            except Exception:
                pass
            return

        def on_triple_tap(self):
            try:
                super(BidiTextInput, self).on_triple_tap()
                Clock.schedule_once(lambda dt: self._show_cut_copy_paste((0,0), self._win))
            except Exception:
                pass
            return
else:
    class BidiTextInput(TextInput):
        delimiters = u' ,\'".;:\n\r\t'
        rtl_font = StringProperty('fonts/Alef-Regular.ttf')
        rtl_font_size = NumericProperty(-1)
        always_blink_cursor = BooleanProperty(False)
        rtl_halign_ignore = BooleanProperty(False)
        halign = OptionProperty('left', options=('left', 'right', 'center', 'justified'))
        valign = OptionProperty('bottom', options=('top', 'middle', 'bottom'))

        def __init__(self, **kwargs):
            # private
            self.last_line_rtl = False
            self.last_line_rtl_font = False
            self.last_ltr_font = ''
            self.topy = 0
            super(BidiTextInput, self).__init__(**kwargs)

        def on_text(self, *args):
            #self._refresh_hint_text()
            pass

        # kivy bugfix - support unicode on android
        def _copy(self, data):
            self._ensure_clipboard()
            # on android leave unicode - otherwise it double encodes to utf-8
            if platform != 'android':
                data = data.encode(self._encoding) + b'\x00'
            from kivy.uix.textinput import Clipboard
            Clipboard.put(data, self._clip_mime_type)
            if data:
                self.cancel_selection()
                self._hide_cut_copy_paste(EventLoop.window)

        # Added support for valign features
        def _update_graphics(self, *largs):
            # Update all the graphics according to the current internal values.
            #
            # This is a little bit complex, cause we have to :
            #     - handle scroll_x
            #     - handle padding
            #     - create rectangle for the lines matching the viewport
            #     - crop the texture coordinates to match the viewport
            #
            # This is the first step of graphics, the second is the selection.

            self.canvas.clear()
            add = self.canvas.add

            lh = self.line_height
            dy = lh + self.line_spacing

            # adjust view if the cursor is going outside the bounds
            sx = self.scroll_x
            sy = self.scroll_y

            # draw labels
            if not self.focus and (not self._lines or (
                    not self._lines[0] and len(self._lines) == 1)):
                rects = self._hint_text_rects
                labels = self._hint_text_labels
                lines = self._hint_text_lines
            else:
                rects = self._lines_rects
                labels = self._lines_labels
                lines = self._lines
            padding_left, padding_top, padding_right, padding_bottom = self.padding
            x = self.x + padding_left
            y = self.top - padding_top + sy
            miny = self.y + padding_bottom
            maxy = self.top - padding_top
            self.topy = self.top - padding_top
            if self.valign[0]=='m':
                th = dy*len(labels) - self.line_spacing
                if th < maxy-miny :
                    y = self.top - padding_top - max(0, ((self.top-padding_top) - (self.y+padding_bottom) - th)/2)
                    self.topy = y
                    sy = self.scroll_y = 0
            elif self.valign[0]=='b':
                th = dy*len(labels) - self.line_spacing
                if th < maxy-miny :
                    y = self.top - padding_top - max(0, ((self.top-padding_top) - (self.y+padding_bottom) - th))
                    self.topy = y
                    sy = self.scroll_y = 0
            for line_num, value in enumerate(lines):
                if miny <= y <= maxy + dy:
                    try:
                        texture = labels[line_num]
                    except:
                        continue
                    size = list(texture.size)
                    texc = texture.tex_coords[:]

                    # calcul coordinate
                    viewport_pos = sx, 0
                    vw = self.width - padding_left - padding_right
                    vh = self.height - padding_top - padding_bottom
                    tw, th = list(map(float, size))
                    oh, ow = tch, tcw = texc[1:3]
                    tcx, tcy = 0, 0

                    # adjust size/texcoord according to viewport
                    if viewport_pos:
                        tcx, tcy = viewport_pos
                        tcx = tcx / tw * (ow)
                        tcy = tcy / th * oh
                    if tw - viewport_pos[0] < vw:
                        tcw = tcw - tcx
                        size[0] = tcw * size[0]
                    elif vw < tw:
                        tcw = (vw / tw) * tcw
                        size[0] = vw
                    if vh < th:
                        tch = (vh / th) * tch
                        size[1] = vh

                    # cropping
                    mlh = lh
                    if y > maxy:
                        vh = (maxy - y + lh)
                        tch = (vh / float(lh)) * oh
                        tcy = oh - tch
                        size[1] = vh
                    if y - lh < miny:
                        diff = miny - (y - lh)
                        y += diff
                        vh = lh - diff
                        tch = (vh / float(lh)) * oh
                        size[1] = vh

                    texc = (
                        tcx,
                        tcy + tch,
                        tcx + tcw,
                        tcy + tch,
                        tcx + tcw,
                        tcy,
                        tcx,
                        tcy)

                    # add rectangle.
                    r = rects[line_num]
                    r.pos = int(x), int(y - mlh)
                    r.size = size
                    r.texture = texture
                    r.tex_coords = texc
                    add(r)

                y -= dy

            self._update_graphics_selection()

        # fix KIVY BUG with min height and padding
        # they mistakenly take the right padding instead of the bottom
        def _get_min_height(self):
            return (len(self._lines) * (self.line_height + self.line_spacing)
                    + self.padding[0] + self.padding[3])
        minimum_height = AliasProperty(_get_min_height, None,
                                       bind=('_lines', 'line_spacing', 'padding',
                                             'font_size', 'font_name', 'password',
                                             'hint_text'))

        def on_always_blink_cursor(self, instance, value):
            if value:
                Clock.schedule_interval(self._do_blink_cursor, 1 / 2.)
            elif not self.focus:
                Clock.unschedule(self._do_blink_cursor)

        def keyboard_on_key_down(self, window, keycode, text, modifiers):
            # hexa = ''
            # for i in range(len(text)) :
            #     hexa = hexa+( '%02x,' % ord(text[i]) )
            # Logger.info('BidiTextInput: [%s] [%s]==<%s> [%s]' % (keycode,text, hexa, modifiers))
            if platform == 'android':
                # this is a bit hackish but it ignores android special softkeyboard
                # strokes.
                if (keycode[0] == 32) and (len(text) == 0) and (not modifiers):
                    return
                if (keycode[0] == 113) and (len(text) == 1) and (ord(text[0]) == 04) and (not modifiers):
                    return
            super(BidiTextInput, self).keyboard_on_key_down(
                window, keycode, text, modifiers)

        def cursor_offset(self):
            offset = super(BidiTextInput, self).cursor_offset()
            viewport_width = self.width - self.padding[0] - self.padding[2]
            if self.halign in ['center'] and self._lines:
                row = min(len(self._lines)-1, self.cursor_row)
                text_width = self._get_text_width(self._lines[row], self.tab_width, self._label_cached)
                if self.last_line_rtl:
                    offset = viewport_width - int((viewport_width - text_width)/2) - offset
                else:
                    offset = offset + int((viewport_width - text_width) / 2)
            else:
                if self.last_line_rtl:
                    offset = viewport_width - offset
            return offset

        def _draw_selection(self, *largs):
            pos, size, line_num, (s1c, s1r), (s2c, s2r),\
                _lines, _get_text_width, tab_width, _label_cached, width,\
                padding_left, padding_right, x, canvas_add, selection_color = largs
            # Draw the current selection on the widget.
            if line_num < s1r or line_num > s2r:
                return
            x, y = pos
            w, h = size
            x1 = x
            x2 = x + w
            if line_num == s1r:
                lines = _lines[line_num]
                x1 -= self.scroll_x
                x1 += _get_text_width(lines[:s1c], tab_width, _label_cached)
            if line_num == s2r:
                lines = _lines[line_num]
                x2 = (x - self.scroll_x) + _get_text_width(lines[:s2c],
                                                           tab_width,
                                                           _label_cached)

            if self._lines:
                row = min(len(self._lines)-1, line_num)
                text_width = self._get_text_width(self._lines[row], self.tab_width, self._label_cached)
                width_minus_padding = text_width
            else:
                width_minus_padding = width - (padding_right + padding_left)
            maxx = x + width_minus_padding
            if not self.last_line_rtl:
                if x1 > maxx:
                    return
                x1 = max(x1, x)
                x2 = min(x2, x + width_minus_padding)
                dx21 = x2 - x1
                if self.halign in ['center'] and self._lines:
                    viewport_width = self.width - self.padding[0] - self.padding[2]
                    x1 += int((viewport_width - text_width) / 2)
            else:
                # Logger.info('BidiTextInput: _draw_selection %d %d %d %d' %(x,x1,x2,maxx))
                x1 = max(x1, x)
                x2 = min(x2, x + width_minus_padding)
                dx21 = x2 - x1
                x1 = self.x + self.width - \
                    self.padding[2] - (x2 - (self.x + self.padding[0]))
                if self.halign in ['center'] and self._lines:
                    viewport_width = self.width - self.padding[0] - self.padding[2]
                    row = min(len(self._lines)-1, line_num)
                    text_width = self._get_text_width(self._lines[row], self.tab_width, self._label_cached)
                    dx21 = min(dx21, text_width)
                    x1 -= int((viewport_width - text_width) / 2)

            canvas_add(Color(*selection_color, group='selection'))
            canvas_add(Rectangle(
                pos=(x1, pos[1]), size=(dx21, size[1]), group='selection'))

        def get_cursor_from_xy(self, x, y):
            #Logger.info('BidiTextInput: get_cursor_from_xy')

            if self.last_line_rtl:
                #Logger.info('BidiTextInput: get_cursor_from_xy %d %d' % (x,y))
                # mirror to the left side
                x = self.x + self.width - \
                    self.padding[2] - (x - (self.x + self.padding[0]))

            padding_top = self.padding[1]
            l = self._lines
            dy = self.line_height + self.line_spacing
            cx = x - self.x
            scrl_y = self.scroll_y
            scrl_x = self.scroll_x
            scrl_y = scrl_y / dy if scrl_y > 0 else 0
            cy = (self.topy + scrl_y * dy) - y
            cy = int(boundary(round(cy / dy - 0.5), 0, len(l) - 1))
            dcx = 0
            _get_text_width = self._get_text_width
            _tab_width = self.tab_width
            _label_cached = self._label_cached

            if self.halign in ['center'] and self._lines:
                    text_width = self._get_text_width(self._lines[cy], self.tab_width, self._label_cached)
                    viewport_width = self.width - self.padding[0] - self.padding[2]
                    cx -= int((viewport_width - text_width) / 2)

            if not self.last_line_rtl:
                for i in range(1, len(l[cy]) + 1):
                    if _get_text_width(l[cy][:i],
                                       _tab_width,
                                       _label_cached) >= cx + scrl_x:
                        break
                    dcx = i
            else:
                for i in range(1, len(l[cy]) + 1):
                    if _get_text_width(l[cy][:i],
                                       _tab_width,
                                       _label_cached) >= cx + scrl_x:
                        break
                    dcx += 1

            cx = dcx
            return cx, cy

        def _get_line_options(self):
            ##options = super(BidiTextInput, self)._get_line_options()
            # Get or create line options, to be used for Label creation
            _label_cached_create = False
            if self._line_options is None:
                _label_cached_create = True
                self._line_options = {
                    'font_size': self.font_size,
                    'font_name': self.font_name,
                    'anchor_x': 'left',
                    'anchor_y': 'top',
                    'padding_x': 0,
                    'padding_y': 0,
                    'padding': (0, 0)}
            options = self._line_options

            #Logger.info('BidiTextInput: _get_line_options, rtl=%s,%s: %s' % (self.last_line_rtl,self.last_line_rtl_font,options))
            options['halign'] = self.halign
            if self.last_line_rtl:
                if self.last_ltr_font == '':
                    self.last_ltr_font = self.font_name
                if self.rtl_font:
                    options['font_name'] = self.rtl_font
                    # update us - for cursor position
                    self.font_name = self.rtl_font
                    if self.rtl_font_size > 0:
                        options['font_size'] = self.rtl_font_size
                if (self.halign != 'center') and (self.halign != 'justified'):
                    options['halign'] = 'right'
                options['padding_x'] = 0
                options['padding'] = [0, options['padding_y']]
                # in order to avoid miss alignment between input object and corelabel
                # (they break line and we dont, give it extra 1px width)
                options['text_size'] = [self.width
                                        -self.padding[0] -self.padding[2], options.get('text_size', [None, None])[1]]

                # don't let the label do the line breaking, we are responsible fo it
                options['force_single_line'] = True

                options['anchor_x'] = 'right'
                options['rtl'] = True
            else:
                if self.last_line_rtl_font:
                    if self.last_ltr_font == '':
                        self.last_ltr_font = self.font_name
                    if self.rtl_font:
                        options['font_name'] = self.rtl_font
                        self.font_name = self.rtl_font
                        if self.rtl_font_size > 0:
                            options['font_size'] = self.rtl_font_size

                elif self.last_ltr_font != '':

                    options['font_name'] = self.last_ltr_font

                    # update us back - for cursor position
                    self.font_name = self.last_ltr_font

                    self.last_ltr_font = ''

                options['rtl'] = False

                # don't let teh label do the line breaking, we are responsible fo it
                options['force_single_line'] = True

                if (self.halign != 'center') and (self.halign != 'justified'):
                    options['halign'] = 'left'
                    options['text_size'] = [None, None]
                else:
                    # in order to avoid miss alignment between input object and corelabel
                    # (they break line and we dont, give it extra 1px width)
                    options['text_size'] = [self.width
                                            -self.padding[0] -self.padding[2], None]

            if _label_cached_create:
                self._label_cached = BidiCoreLabel(**options)

            ##Logger.info('OPTIONSSSS %s' % options)
            self._line_options = options
            return options

        def _create_line_label_super(self, text, hint=False):
            # Create a label from a text, using line options
            ntext = text.replace(u'\n', u'').replace(u'\t', u' ' * self.tab_width)
            if self.password and not hint:  # Don't replace hint_text with *
                ntext = u'*' * len(ntext)
            kw = self._get_line_options()
            cid = '%s\0%s' % (ntext, str(kw))
            texture = Cache_get('textinput.label', cid)

            if not texture:
                # FIXME right now, we can't render very long line...
                # if we move on "VBO" version as fallback, we won't need to
                # do this.  try to found the maximum text we can handle
                label = None
                label_len = len(ntext)
                ld = None
                while True:
                    try:
                        rtext = ntext[:label_len]
                        label = BidiCoreLabel(text=rtext, **kw)
                        label.refresh()
                        if ld is not None and ld > 2:
                            ld = int(ld / 2)
                            label_len += ld
                        else:
                            break
                    except:
                        # exception happen when we tried to render the text
                        # reduce it...
                        if not ld:
                            ld = len(ntext)
                        if ld == 0:
                            break
                        ld = int(ld / 2)
                        if ld < 2 and label_len:
                            label_len -= 1
                        label_len -= ld
                        continue

                # ok, we found it.
                texture = label.texture
                Cache_append('textinput.label', cid, texture)
            return texture


        def _update_last_line_rtl(self, text):
            # check bidi font and direction
            base_level, has_rtl = get_display_hasrtl(text)
            right_to_left = (base_level != 0)

            #Logger.info('BidiTextInput: rtl=%s %s %s: [%s] [%s]' % (right_to_left,base_level,has_rtl,text,rtext))
            self.last_line_rtl = right_to_left or self.last_line_rtl
            self.last_line_rtl_font = (self.last_line_rtl) or has_rtl

            # ignore left to right direction
            if self.rtl_halign_ignore:
                self.last_line_rtl = False

        def _set_line_text(self, line_num, text):
            prev_rtl = self.last_line_rtl
            self._update_last_line_rtl(text)
            if prev_rtl != self.last_line_rtl:
                # trigger update on text - we changed the rtl flag
                self._trigger_refresh_text()

            super(BidiTextInput, self)._set_line_text(line_num, text)

        def _refresh_text(self, text, *largs):
            self._update_last_line_rtl(text)
            super(BidiTextInput, self)._refresh_text(text, *largs)

        def _create_line_label(self, text, hint=False):
            # don't process hint_text when not needed
            if hint and not (not self._lines or (not self._lines[0] and len(self._lines) == 1)):
                return

            return self._create_line_label_super(text, hint)

        def _refresh_hint_text(self):
            _lines, self._hint_text_flags = self._split_smart(self.hint_text)
            _hint_text_labels = []
            _hint_text_rects = []
            _create_label = self._create_line_label

            for x in _lines:
                lbl = _create_label(x, hint=True)
                if lbl:
                    _hint_text_labels.append(lbl)
                    _hint_text_rects.append(Rectangle(size=lbl.size))

            self._hint_text_lines = _lines
            self._hint_text_labels = _hint_text_labels
            self._hint_text_rects = _hint_text_rects

            # Remember to update graphics
            self._trigger_update_graphics()

        def _get_cursor(self):
            return self._cursor

        def _set_cursor(self, pos):
            if not self.last_line_rtl:
                padding_left = self.padding[0]
                padding_right = self.padding[2]
                viewport_width = self.width - padding_left - padding_right ##self.font_size*1
                sx = self.scroll_x
                _set_cursor_success = super(BidiTextInput, self)._set_cursor(pos)
                offset = self.cursor_offset()
                if _set_cursor_success is True:
                    if self.last_line_rtl_font:
                        if sx == 0:
                            self.scroll_x = 0
                    else:
                        if offset >= viewport_width + sx:
                            self.scroll_x = offset - viewport_width
                        elif offset >= viewport_width and ((offset-sx) % viewport_width < self.font_size):
                            self.scroll_x = offset - viewport_width
                        elif ((offset-sx) % viewport_width < self.font_size):
                            self.scroll_x = 0
                        elif offset < sx:
                            self.scroll_x = offset
                    return True
                return

            if not self._lines:
                self._trigger_refresh_text()
                return
            l = self._lines
            cr = boundary(pos[1], 0, len(l) - 1)
            cc = boundary(pos[0], 0, len(l[cr]))
            cursor = cc, cr
            if self._cursor == cursor:
                return

            self._cursor = cursor

            # adjust scrollview to ensure that the cursor will be always inside our
            # viewport.
            padding_left = self.padding[0]
            padding_right = self.padding[2]
            viewport_width = self.width - padding_left - padding_right
            sx = self.scroll_x
            offset = self.cursor_offset()

            # if offset is outside the current bounds, reajust
            # reverse offset so reverse scroll...
            scroll_x = sx
            if offset > viewport_width + sx:
                scroll_x = offset
            elif offset < 0:
                scroll_x = 0 #offset
            elif offset < sx:
                scroll_x = offset - viewport_width

            # do the same for Y
            # this algo try to center the cursor as much as possible
            dy = self.line_height + self.line_spacing
            offsety = cr * dy
            sy = self.scroll_y
            padding_top = self.padding[1]
            padding_bottom = self.padding[3]
            viewport_height = self.height - padding_top - padding_bottom - dy
            if offsety > viewport_height + sy:
                sy = offsety - viewport_height
            if offsety < sy:
                sy = offsety

            # update only now - since this function is actually already bounded to the scroll property
            self.scroll_y = sy
            self.scroll_x = scroll_x

            return True

        cursor = AliasProperty(_get_cursor, _set_cursor)

        def _get_cursor_pos(self):
            # if not self.last_line_rtl:
            #     return super(BidiTextInput, self)._get_cursor_pos()

            # return the current cursor x/y from the row/col
            dy = self.line_height + self.line_spacing
            padding_left = self.padding[0]
            padding_top = self.padding[1]
            left = self.x + padding_left

            #
            padding_left, padding_top, padding_right, padding_bottom = self.padding
            sy = self.scroll_y
            miny = self.y + padding_bottom
            maxy = self.top - padding_top

            # recalc topy
            top = self.top - padding_top
            if self.valign[0]=='m':
                th = dy*len(self._lines_labels) - self.line_spacing
                if th < maxy-miny :
                    y = self.top - padding_top - max(0, ((self.top-padding_top) - (self.y+padding_bottom) - th)/2)
                    top = y
            elif self.valign[0]=='b':
                th = dy*len(self._lines_labels) - self.line_spacing
                if th < maxy-miny :
                    y = self.top - padding_top - max(0, ((self.top-padding_top) - (self.y+padding_bottom) - th))
                    top = y

            #top = self.topy
            y = top + self.scroll_y
            y -= self.cursor_row * dy
            x, y = left + self.cursor_offset() - self.scroll_x, y
            if x < left:
                self.scroll_x = 0
                x = left
            if y > top:
                y = top
                self.scroll_y = 0
            return x, y
        cursor_pos = AliasProperty(_get_cursor_pos, None, bind=(
            'cursor', 'padding', 'pos', 'size', 'focus','_lines',
            'scroll_x', 'scroll_y'))

        # fix KIVY BUG
        # new line check with self.width-padding instead of just self.width
        def insert_text(self, substring, from_undo=False):
            '''Insert new text at the current cursor position. Override this
            function in order to pre-process text for input validation.
            '''
            if self.readonly or not substring:
                return

            mode = self.input_filter
            if mode is not None:
                chr = type(substring)
                if chr is bytes:
                    int_pat = self._insert_int_patb
                else:
                    int_pat = self._insert_int_patu

                if mode == 'int':
                    substring = re.sub(int_pat, chr(''), substring)
                elif mode == 'float':
                    if '.' in self.text:
                        substring = re.sub(int_pat, chr(''), substring)
                    else:
                        substring = '.'.join([re.sub(int_pat, chr(''), k) for k
                                              in substring.split(chr('.'), 1)])
                else:
                    substring = mode(substring, from_undo)
                if not substring:
                    return

            self._hide_handles(EventLoop.window)

            if not from_undo and self.multiline and self.auto_indent \
                    and substring == u'\n':
                substring = self._auto_indent(substring)

            cc, cr = self.cursor
            sci = self.cursor_index
            ci = sci()
            text = self._lines[cr]
            len_str = len(substring)
            new_text = text[:cc] + substring + text[cc:]
            self._set_line_text(cr, new_text)

            wrap = (self._get_text_width(
                new_text,
                self.tab_width,
                self._label_cached) >= self.width - self.padding[0] - self.padding[2] )
            if len_str > 1 or substring == u'\n' or wrap:
                # Avoid refreshing text on every keystroke.
                # Allows for faster typing of text when the amount of text in
                # TextInput gets large.

                start, finish, lines,\
                    lineflags, len_lines = self._get_line_from_cursor(cr, new_text)
                # calling trigger here could lead to wrong cursor positioning
                # and repeating of text when keys are added rapidly in a automated
                # fashion. From Android Keyboard for example.
                self._refresh_text_from_property('insert', start, finish, lines,
                                                 lineflags, len_lines)

            self.cursor = self.get_cursor_from_index(ci + len_str)
            # handle undo and redo
            self._set_unredo_insert(ci, ci + len_str, substring, from_undo)

        # adjust specifically with value
        def _tokenize(self, text):
            # Tokenize a text string from some delimiters
            if text is None:
                return
            delimiters = self.delimiters # u' ,\'".;:\n\r\t'
            oldindex = 0
            for index, char in enumerate(text):
                if char not in delimiters:
                    continue
                if oldindex != index:
                    yield text[oldindex:index]
                yield text[index:index + 1]
                oldindex = index + 1
            yield text[oldindex:]

        # Bug in Kivy split line, if the word is longer than the max width,
        # we need to split the word anyhow
        def _split_smart(self, text):
            # Do a "smart" split. If autowidth or autosize is set,
            # we are not doing smart split, just a split on line break.
            # Otherwise, we are trying to split as soon as possible, to prevent
            # overflow on the widget.

            padding_left = self.padding[0]
            padding_right = self.padding[2]
            width = self.width - padding_left - padding_right

            # depend of the options, split the text on line, or word
            if not self.multiline or width <= 0:
                lines = text.split(u'\n')
                lines_flags = [0] + [FL_IS_NEWLINE] * (len(lines) - 1)
                return lines, lines_flags

            # no autosize, do wordwrap.
            x = flags = 0
            line = []
            lines = []
            lines_flags = []
            _join = u''.join
            lines_append, lines_flags_append = lines.append, lines_flags.append
            text_width = self._get_text_width
            _tab_width, _label_cached = self.tab_width, self._label_cached

            # try to add each word on current line.
            for word in self._tokenize(text):
                #if word==u'':
                #    continue
                is_newline = (word == u'\n')
                w = text_width(word, _tab_width, _label_cached)
                # if we have more than the width, or if it's a newline,
                # push the current line, and create a new one
                if (x + w > width) or is_newline:
                    # now we check if we already started a new line and
                    # the word is still to big
                    if x==0 or w>width:
                        # if the word is too long commit the current and start a new one
                        if w>width and line:
                            lines_append(_join(line))
                            lines_flags_append(flags)
                            flags = 0
                            line = []
                            x = 0
                        # try to find the max chars that fits in the line
                        newword = word
                        wordfound = True
                        while len(newword)>0 and wordfound:
                            wordfound = False
                            for i in range(0,len(newword)):
                                word = newword[0:len(newword)-i]
                                w = text_width(word, _tab_width, _label_cached)
                                if x + w <= width:
                                    newword = newword[len(newword)-i:]
                                    wordfound = True
                                    if newword:
                                        lines_append(_join(word))
                                        lines_flags_append(flags)
                                        flags = 0
                                        line = []
                                        x = 0
                                    break
                    elif line:
                        lines_append(_join(line))
                        lines_flags_append(flags)
                        flags = 0
                        line = []
                        x = 0
                    else:
                        x += w
                        line.append(word)
                if is_newline:
                    flags |= FL_IS_NEWLINE
                else:
                    x += w
                    line.append(word)
            if line or flags & FL_IS_NEWLINE:
                lines_append(_join(line))
                lines_flags_append(flags)

            #if not lines:
            #    lines = [u'']
            return lines, lines_flags

        # they have some bugs in their code,
        # we just protect against exceptions here
        def _show_cut_copy_paste(self, pos, win, parent_changed=False, mode='', *l):
            try:
                # position should always be above selectors
                s1c, s1r = self.get_cursor_from_index(self._selection_to)
                s2c, s2r = self.get_cursor_from_index(self._selection_from)
                c,r = (s1c, s1r) if s1r<s2r else (s2c, s2r)
                pos = ( int(self.cursor_pos[0]),
                        int(self._lines_rects[r].pos[1] + self._lines_rects[r].size[1]/2) )
                super(BidiTextInput, self)._show_cut_copy_paste(
                    pos, win, parent_changed, mode, *l)
            except Exception:
                pass
            return

        def delete_selection(self, from_undo=False):
            super(BidiTextInput, self).delete_selection(from_undo)
            self._hide_cut_copy_paste(EventLoop.window)

        def _show_handles(self, win):
            try:
                super(BidiTextInput, self)._show_handles(win)
            except Exception:
                pass
            return

        def _hide_cut_copy_paste(self, win=None):
            try:
                super(BidiTextInput, self)._hide_cut_copy_paste(win)
            except Exception:
                pass
            return

        def _hide_handles(self, win=None):
            try:
                super(BidiTextInput, self)._hide_handles(win)
            except Exception:
                pass
            return

        def _position_handles(self, mode='both'):
            try:
                super(BidiTextInput, self)._position_handles(mode)
            except Exception:
                pass
            return

        def _handle_move(self, instance, touch):
            try:
                super(BidiTextInput, self)._handle_move(instance, touch)
            except Exception:
                pass
            return

        def _handle_released(self, instance):
            try:
                super(BidiTextInput, self)._handle_released(instance)
            except Exception:
                pass
            return

        def _handle_pressed(self, instance):
            try:
                super(BidiTextInput, self)._handle_pressed(instance)
            except Exception:
                pass
            return

        def on_double_tap(self):
            try:
                super(BidiTextInput, self).on_double_tap()
                Clock.schedule_once(lambda dt: self._show_cut_copy_paste((0,0), EventLoop.window))
            except Exception:
                pass
            return

        def on_triple_tap(self):
            try:
                super(BidiTextInput, self).on_triple_tap()
                Clock.schedule_once(lambda dt: self._show_cut_copy_paste((0,0), EventLoop.window))
            except Exception:
                pass
            return
