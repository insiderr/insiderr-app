
from kivy.uix.gridlayout import GridLayout, GridLayoutException
from kivy.uix.layout import Layout
from kivy.properties import VariableListProperty, NumericProperty, ReferenceListProperty, BooleanProperty
from kivy.logger import Logger


class ListLayoutInt(Layout):
    spacing = VariableListProperty([0, 0], length=2)
    padding = VariableListProperty([0, 0, 0, 0], length=4)
    minimum_width = NumericProperty(0)
    minimum_height = NumericProperty(0)
    minimum_size = ReferenceListProperty(minimum_width, minimum_height)

    def update_minimum_width(self):
        minimum_width = 9999
        for w in self.children:
            minimum_width = min(minimum_width, w.width)
        self.minimum_width = minimum_width

    def add_widget(self, widget, index=0):
        # update widget position relative to our own.
        widget.x = int(self.x+self.padding[0]+widget.x)
        if index != 0:
            widget.y = int(self.y+self.minimum_height)
        else:
            if len(self.children) > 0 and hasattr(self.children[0], 'stick_bottom') and self.children[0].stick_bottom:
                widget.y = int(self.children[0].y + self.children[0].height + self.spacing[1])
                index = 1
            else:
                widget.y = int(self.y)
            h = widget.height+self.spacing[1]
            for w in self.children:
                if hasattr(w, 'stick_bottom') and w.stick_bottom:
                    continue
                w.y += h
        Logger.info('ListLayoutInt -- %s %s %s %s' % (self.x, self.y, widget.height, self.minimum_height))
        # udate minimum width / height
        self.minimum_width = min(self.minimum_width, widget.width)
        if len(self.children) == 0:
            self.minimum_height = 2*self.spacing[1]+widget.height
        else:
            self.minimum_height += self.spacing[1]+widget.height
        index = max(0, min(len(self.children), index))
        # actuall insert into children list and canvas
        #self.children.insert(index, widgetBooleanProperty)
        super(ListLayoutInt, self).add_widget(widget, index)
        self.height = self.minimum_height
        self.width = self.minimum_width
        return True

    def remove_widget(self, widget):
        if widget not in self.children:
            return
        # find out from where we need to update the y location (i.e after the widget)
        #self.children.remove(widget)
        super(ListLayoutInt, self).remove_widget(widget)
        self.update_minimum_width()
        if len(self.children) == 0:
            self.minimum_height = 0
        else:
            self.minimum_height -= self.spacing[1]+widget.height
        self.width = self.minimum_width
        self.height = self.minimum_height
        return True

    def do_layout(self, *largs):
        pass


class GridLayoutInt(GridLayout):
    order_vertical = BooleanProperty(False)

    def do_layout(self, *largs):
        self.update_minimum_size()
        if self._cols is None:
            return
        if self.cols is None and self.rows is None:
            raise GridLayoutException('Need at least cols or rows constraint.')

        children = self.children
        len_children = len(children)
        if len_children == 0:
            return

        # speedup
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        spacing_x, spacing_y = self.spacing
        selfx = self.x
        selfw = self.width
        selfh = self.height

        # resolve size for each column
        if self.col_force_default:
            cols = [self.col_default_width] * len(self._cols)
            for index, value in self.cols_minimum.items():
                cols[index] = value
        else:
            cols = self._cols[:]
            cols_sh = self._cols_sh
            cols_weigth = sum([x for x in cols_sh if x])
            strech_w = max(0, selfw - self.minimum_width)
            for index in range(len(cols)):
                # if the col don't have strech information, nothing to do
                col_stretch = cols_sh[index]
                if col_stretch is None:
                    continue
                # calculate the column stretch, and take the maximum from
                # minimum size and the calculated stretch
                col_width = cols[index]
                col_width = max(col_width,
                                strech_w * col_stretch / cols_weigth)
                cols[index] = col_width

        # same algo for rows
        if self.row_force_default:
            rows = [self.row_default_height] * len(self._rows)
            for index, value in self.rows_minimum.items():
                rows[index] = value
        else:
            rows = self._rows[:]
            rows_sh = self._rows_sh
            rows_weigth = sum([x for x in rows_sh if x])
            strech_h = max(0, selfh - self.minimum_height)
            for index in range(len(rows)):
                # if the row don't have strech information, nothing to do
                row_stretch = rows_sh[index]
                if row_stretch is None:
                    continue
                # calculate the row stretch, and take the maximum from minimum
                # size and the calculated stretch
                row_height = rows[index]
                row_height = max(row_height,
                                 strech_h * row_stretch / rows_weigth)
                rows[index] = row_height

        #reposition every child - order horizontally or vertically
        if self.order_vertical:
            i = len_children - 1
            x = selfx + padding_left
            for col_width in cols:
                y = self.top - padding_top
                for row_height in rows:
                    if i < 0:
                        break
                    c = children[i]
                    c.x = int(x)
                    c.y = int(y - row_height)
                    c.width = int(col_width)
                    c.height = int(row_height)
                    i -= 1
                    y -= row_height + spacing_y
                x = x + col_width + spacing_x
        else:
            i = len_children - 1
            y = self.top - padding_top
            for row_height in rows:
                x = selfx + padding_left
                for col_width in cols:
                    if i < 0:
                        break
                    c = children[i]
                    c.x = int(x)
                    c.y = int(y - row_height)
                    c.width = int(col_width)
                    c.height = int(row_height)
                    i -= 1
                    x = x + col_width + spacing_x
                y -= row_height + spacing_y
