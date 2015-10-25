
from kivy.logger import Logger
from kivy.uix.label import Label
from kivy.core.text import Label as CoreLabel
from kivy.core.text.markup import MarkupLabel as CoreMarkupLabel
from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from functools import partial
from copy import copy
from modules.core.bidi.algorithm import get_display, get_display_hasrtl
from re import split

class BidiMarkupLabel(CoreMarkupLabel):
    def __init__(self, **kwargs):
        super(BidiMarkupLabel, self).__init__(**kwargs)
        self.rtl = kwargs.get('rtl', False)

    def _pre_render_label(self, word, options, lines):
        # precalculate id/name
        if not self.fontid in self._cache_glyphs:
            self._cache_glyphs[self.fontid] = {}
        cache = self._cache_glyphs[self.fontid]

        # verify that each glyph have size
        glyphs = list(set(word))
        glyphs.append(' ')
        get_extents = self.get_extents
        for glyph in glyphs:
            if not glyph in cache:
                cache[glyph] = get_extents(glyph)

        glyph_space_w = cache[' '][0]

        # get last line information
        if len(lines):
            line = lines[-1]
        else:
            # line-> line width, line height, is_last_line,
            # is_first_line, words words -> (w, h, word)...
            line = [0, 0, 0, 1, []]
            lines.append(line)

        # extract user limitation
        uw, uh = self.text_size

        #Logger.info('BIDI: %s -- <%s>' % (uw,word))

        # split the word
        default_line_height = get_extents(' ')[1] * self.options['line_height']
        list_of_parts = split(r'( |\n)', word)

        # if it's rtl - we need to reverse the words order
        if self.rtl:
            list_of_parts.reverse()

        for part in list_of_parts:

            if part == '':
                continue

            if part == '\n':
                # never end a line with a space
                # so check the current line - if it has a space - remove it
                if self.rtl:
                    if len(lines) > 0 and len(lines[-1]) > 0 and len(lines[-1][4]) > 0 \
                            and len(lines[-1][4][0]) > 0 and lines[-1][4][0][2][0] == ' ':
                        lines[-1][4].pop(0)
                        lines[-1][0] -= glyph_space_w
                else:
                    if len(lines) > 0 and len(lines[-1]) > 0 and len(lines[-1][4]) > 0 \
                            and len(lines[-1][4][-1]) > 0 and lines[-1][4][-1][2][0] == ' ':
                        lines[-1][4].pop()
                        lines[-1][0] -= glyph_space_w

                # put a new line!
                line = [0, default_line_height, 0, 1, []]
                # skip last line for justification.
                if lines:
                    lines[-1][2] = 1
                    lines[-1]
                lines.append(line)
                continue

            # get current line information
            lw, lh = line[:2]

            # calculate the size of the part
            # (extract all extents of the part,
            # calculate width through extents due to kerning
            # and get the maximum height)
            pg = [cache[g] for g in part]
            pw = get_extents(part)[0]
            ph = max([g[1] for g in pg])
            ph = ph * self.options['line_height']
            options = copy(options)

            # check if the part can be put in the line
            if uw is None or lw + pw < uw:
                # no limitation or part can be contained in the line
                # then append the part to the line
                if self.rtl:
                    line[4].insert(0, (pw, ph, part, options))
                else:
                    line[4].append((pw, ph, part, options))
                # and update the line size
                line[0] += pw
                line[1] = max(line[1], ph)
            else:
                # never end a line with a space
                # so check the current line - if it has a space - remove it
                if self.rtl:
                    if len(lines) > 0 and len(lines[-1]) > 0 and len(lines[-1][4]) > 0 \
                            and len(lines[-1][4][0]) > 0 and lines[-1][4][0][2][0] == ' ':
                        lines[-1][4].pop(0)
                        lines[-1][0] -= glyph_space_w
                else:
                    if len(lines) > 0 and len(lines[-1]) > 0 and len(lines[-1][4]) > 0 \
                            and len(lines[-1][4][-1]) > 0 and lines[-1][4][-1][2][0] == ' ':
                        lines[-1][4].pop()
                        lines[-1][0] -= glyph_space_w

                # part can't be put in the line, do a new one...
                if part[0] != ' ':
                    line = [pw, ph, 0, 0, [(pw, ph, part, options)]]
                else:
                    line = [0, default_line_height, 0, 1, []]

                lines.append(line)

        # set last_line to be skipped for justification
        lines[-1][2] = 1


class BidiCoreLabel(CoreLabel):
    delimiters = u' \n\r\t'  #u' ,\'".;:\n\r\t'

    def __init__(self, **kwargs):
        self.rtl = kwargs.get('rtl', False)
        self.force_single_line = kwargs.get('force_single_line', False)
        super(BidiCoreLabel, self).__init__(**kwargs)

    def shorten(self, text, margin=2):
        # Just a tiny shortcut
        textwidth = self.get_extents
        if self.text_size[0] is None:
            width = 0
        else:
            width = int(self.text_size[0])

        letters = text.strip()
        if not self.rtl:
            while textwidth(letters+'...')[0] > width:
                letters = letters[:-1]
        else:
            while textwidth('...'+letters)[0] > width:
                letters = letters[1:]

        if not self.rtl:
            return type(text)('{0}...').format(letters)
        else:
            return type(text)('...{0}').format(letters)

    # Bug kivy render splits the lines on a glygh based calculation
    # ignoring kerning. the rest of the infrastructure calculates per word.
    # which is the correct way, so we implement it here
    def _split_smart(self, text):
        # Do a "smart" split. If autowidth or autosize is set,
        # we are not doing smart split, just a split on line break.
        # Otherwise, we are trying to split as soon as possible, to prevent
        # overflow on the widget.

        # depend of the options, split the text on line, or word
        if not self.text_size[0]:
            lines = text.split(u'\n')
            return lines

        # return the text width + tab support
        def text_width(text, _tab_width):
            text = text.replace('\t', ' ' * _tab_width)
            w, h = self.get_extents(text)
            return w

        def _tokenize(text):
            # Tokenize a text string from some delimiters
            if text is None:
                return
            delimiters = self.delimiters#u' ,\'".;:\n\r\t'
            oldindex = 0
            for index, char in enumerate(text):
                if char not in delimiters:
                    continue
                if oldindex != index:
                    yield text[oldindex:index]
                yield text[index:index + 1]
                oldindex = index + 1
            yield text[oldindex:]

        # no autosize, do wordwrap.
        FL_IS_NEWLINE = 1
        x = flags = 0
        line = []
        lines = []
        _join = u''.join
        lines_append = lines.append
        width = self.text_size[0]
        _tab_width = 4 ##

        # try to add each word on current line.
        for word in _tokenize(text):
            #if word==u'':
            #    continue
            is_newline = (word == u'\n')
            w = text_width(word, _tab_width)
            # if we have more than the width, or if it's a newline,
            # push the current line, and create a new one
            if (x + w > width) or is_newline:
                # now we check if we already started a new line and
                # the word is still to big
                if x==0 or w>width:
                    # if the word is too long commit the current and start a new one
                    if w>width and line:
                        lines_append(_join(line))
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
                            w = text_width(word, _tab_width)
                            if x + w <= width:
                                newword = newword[len(newword)-i:]
                                wordfound = True
                                if newword:
                                    lines_append(_join(word))
                                    flags = 0
                                    line = []
                                    x = 0
                                break
                elif line:
                    lines_append(_join(line))
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

        # test if we need to reverse order of words:
        if self.rtl:
            for i,l in enumerate(lines):
                #rtext = reverse_tokenize(l)
                rtext, rtl, has_rtl = get_display(l, base_dir='R')
                lines[i] = rtext

        return lines

    def render(self, real=False):
        '''Return a tuple (width, height) to create the image
        with the user constraints.

        2 differents methods are used:
          * if the user does not set the width, split the line
            and calculate max width + height
          * if the user sets a width, blit per glyph
        '''

        options = self.options
        render_text = self._render_text
        get_extents = self.get_extents
        uw, uh = self.text_size
        max_lines = int(options.get('max_lines', 0))
        w, h = 0, 0
        x, y = 0, 0
        if real:
            self._render_begin()
            halign = options['halign']
            valign = options['valign']
            if valign == 'bottom':
                y = self.height - self._internal_height
            elif valign == 'middle':
                y = int((self.height - self._internal_height) / 2)
        else:
            self._internal_height = 0

        glyph_space_w = get_extents(' ')[0]

        # no width specified, faster method
        if uw is None:
            index = 0
            text, rtl, has_rtl = get_display(self.text, base_dir='L')

            for line in text.split('\n'):
                index += 1
                if max_lines > 0 and index > max_lines:
                    break
                lw, lh = get_extents(line)
                lh = lh * options['line_height']
                if real:
                    x = 0
                    if halign[0] == 'c':
                        # center
                        x = int((self.width - lw) / 2.)
                    elif halign[0] == 'r':
                        # right
                        x = int(self.width - lw)
                    if len(line):
                        render_text(line, x, y)
                    y += int(lh)
                else:
                    w = max(w, int(lw))
                    self._internal_height += int(lh)
            h = self._internal_height if uh is None else uh

        # constraint
        else:

            text = self.text
            width = uw + int(options.get('padding_x', 0)) * 2

            # Shorten the text that we actually display
            if (options['shorten']):
                last_word_width = get_extents(text[text.rstrip().rfind(' '):])[0]
                if get_extents(text)[0] > uw - last_word_width:
                    text = self.shorten(text)

            index = 0
            if self.force_single_line:
                # test if we need to reverse order of words:
                if self.rtl:
                    rtext, rtl, has_rtl = get_display(text, base_dir='R')
                    lines = [rtext]
                else:
                    rtext, rtl, has_rtl = get_display(text, base_dir='L')
                    lines = [rtext]
            else:
                lines = self._split_smart(text)
            for line in lines:
                index += 1
                if max_lines > 0 and index > max_lines:
                    break
                lw, lh = get_extents(line)
                lh = lh * options['line_height']
                if real:
                    x = 0
                    if halign[0] == 'c':
                        # center
                        x = int((width - lw) / 2.)
                    elif halign[0] == 'r':
                        # right
                        x = int(width - lw)
                    elif halign[0] == 'j':
                        # justify, recalc avg spaces
                        words = line.split()
                        sw = get_extents(' ')[0]
                        _spaces = len(words)-1
                        if _spaces > 0:
                            just_space = (((uw - lw + sw*_spaces) * 1.) / (_spaces * 1.))
                        else:
                            just_space = 0
                        # render per word with new spaces
                        for word in words:
                            cw = get_extents(word)[0]
                            render_text(word, x, y)
                            x += cw + just_space
                        line = ''
                    if len(line):
                        x = max(1, x)
                        render_text(line, x, y)
                    y += int(lh)
                else:
                    w = uw
                    if (self.rtl and self.force_single_line and not real):
                        w = max(lw,uw)
                    self._internal_height += int(lh)
            h = self._internal_height if uh is None else uh

        if not real:
            # was only the first pass
            # return with/height
            w = int(max(w, 1))
            h = int(max(h, 1))
            return w, h

        # get data from provider
        data = self._render_end()
        assert(data)

        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            self.texture.blit_data(data)


class BidiLabel(Label):
    rtl_font = StringProperty('fonts/Alef-Regular.ttf')
    rtl_halign_ignore = BooleanProperty(False)
    rtl_font_size = NumericProperty(-1)

    def __init__(self, **kwargs):
        # private
        self.last_line_rtl = False
        self.line_rtl = False

        self.rtl_font = kwargs.get('rtl_font', self.rtl_font)
        self.rtl_font_size = kwargs.get('rtl_font_size', self.rtl_font_size)
        self.rtl_halign_ignore = kwargs.get(
            'rtl_halign_ignore', self.rtl_halign_ignore)

        dkw = {}
        value = kwargs.get('text', '')
        self.line_rtl = False
        if value:
            rtl, has_rtl = get_display_hasrtl(value)
            self.line_rtl = (rtl != 0) or (has_rtl)

        super(BidiLabel, self).__init__(**kwargs)
        dkw['rtl_font'] = partial(self._trigger_texture_update, 'rtl_font')
        dkw['rtl_font_size'] = partial(self._trigger_texture_update, 'rtl_font_size')
        self.bind(**dkw)
        dkw['rtl'] = self.line_rtl

    def _trigger_texture_update(self, name=None, source=None, value=None):
        # check if the label core class need to be switch to a new one
        if name == 'markup':
            self._create_label()
        if source:
            if name == 'text':
                rtl, has_rtl = get_display_hasrtl(value)
                self.line_rtl = (rtl != 0) or (has_rtl)

                if (self.line_rtl != self.last_line_rtl):
                    self._create_label()

                # if self.line_rtl:
                #     rtext, _ = remove_leading_spaces(rtext)
                #     print 'BEFORE %s' % self._label.text.encode('utf-8')
                #     print 'AFTER %s' % rtext.encode('utf-8')
                #     self._label.text = rtext
                # else:
                self._label.text = value

            elif name == 'text_size':
                self._label.usersize = value
            elif name == 'font_size':
                self._label.options[name] = value
                if self.rtl_font_size < 0:
                    self.rtl_font_size = value
            elif name == 'rtl_font':
                if self.line_rtl:
                    self._label.options['font_name'] = value
                self.rtl_font = value
            elif name == 'rtl_font_size':
                if self.line_rtl:
                    self._label.options['font_size'] = value
                self.rtl_font_size = value
            else:
                self._label.options[name] = value

        self._trigger_texture()

    def _create_label(self):

        # create the core label class according to markup value
        if self._label is not None:
            cls = self._label.__class__
        else:
            cls = None
        markup = self.markup

        if (self.line_rtl != self.last_line_rtl) or \
           (markup and cls is not CoreMarkupLabel) or \
           (not markup and cls is not CoreLabel):

            self.last_line_rtl = self.line_rtl

            # markup have change, we need to change our rendering method.
            d = Label._font_properties
            dkw = dict(list(zip(d, [getattr(self, x) for x in d])))

            if self.line_rtl:
                dkw['font_name'] = self.rtl_font
                if self.rtl_font_size > 0:
                    dkw['font_size'] = self.rtl_font_size
                if not self.rtl_halign_ignore:
                    if self.halign == 'left':
                        dkw['halign'] = 'right'
                    elif self.halign == 'right':
                        dkw['halign'] = 'left'
                    # elif self.halign=='justify':
                    #     dkw['halign']='right'
                dkw['rtl'] = True
                #rtext, rtl, has_rtl = get_display(dkw['text'])
                ##dkw['text'] = rtext
                ###dkw['text_size'] = [self.width - self.font_size, None]
                dkw['text_size'] = [self.width, None]

            if markup:
                self._label = BidiMarkupLabel(**dkw)
            else:
                self._label = BidiCoreLabel(**dkw)
