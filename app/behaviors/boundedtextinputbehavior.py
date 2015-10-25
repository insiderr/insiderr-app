from kivy.properties import NumericProperty


class BoundedTextInputBehavior(object):
    max_chars = NumericProperty(None, allownone=True)

    def insert_text(self, substring, from_undo=False):
        if self.max_chars is not None and not from_undo and (len(unicode(self.text.decode('utf-8')))+len(substring) > self.max_chars):
            return
        super(BoundedTextInputBehavior, self).insert_text(substring, from_undo)