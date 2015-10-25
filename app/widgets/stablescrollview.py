from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.metrics import sp
from functools import partial
from time import time
from theme import _scale_to_theme_dpi


# TODO: add support for horizontal scroll


class StableScrollView(ScrollView):
    class BBox():
        def __init__(self, topx, topy, bottomx, bottomy):
            self.top = topy
            self.x = topx
            self.right = bottomx
            self.y = bottomy

    ''' Stabilize view when changing child size
        currently we support size increase
    '''
    # 1.0 equals one page from top/bottom 2.0 = two pages etc...
    hit_top_threshold = NumericProperty(None, allownone=True)
    hit_bottom_threshold = NumericProperty(None, allownone=True)
    expand_stopped_bbox = NumericProperty(0)
    min_stop_velocity = NumericProperty(50)
    overscroll_event_threshold = NumericProperty(0.1)

    __events__ = ('on_hit_bottom', 'on_hit_top', 'on_stopped')

    def __init__(self, **kwargs):
        self.prev_stop_pos = -1.0
        self.stop_pos = 0.0
        self.prev_vp_height = 0
        self.last_remove_pos = [0, 0]
        self.last_addition_pos = [0, 0]
        self.border_event_dispatched = dict((event, False) for event in self.__events__)
        self.border_event_fired = dict((event, False) for event in self.__events__)
        super(StableScrollView, self).__init__(**kwargs)
        self.scroll_timeout = 80
        self.scroll_distance = int(_scale_to_theme_dpi(self.scroll_distance*1.333))

    def viewport_pos_from_child_pos(self, pos):
        vp = self._viewport
        if not vp:
            return pos
        sh = vp.height - self.height
        sw = vp.width - self.width
        return [pos[0]-self.scroll_x*sw, pos[1]-self.scroll_y*sh]

    # top,left corner = 0,1
    # bottom,right corner = 1,0
    # bbox = (left, top, right, bottom)
    def _get_pure_viewbox(self):
        bbox = [-self.effect_x.value, -self.effect_y.value+self.height, -self.effect_x.value+self.width, -self.effect_y.value]
        return bbox

    def get_viewbox(self):
        bbox = self._get_pure_viewbox()
        if self.expand_stopped_bbox > 0:
            h = abs(bbox[1]-bbox[3])
            leftover_fromtop = max(0, 0-int(bbox[3]-h*self.expand_stopped_bbox))
            leftover_frombottom = max(0, int(bbox[1]+h*self.expand_stopped_bbox)-self._viewport.height)
            bbox[3] = max(int(bbox[3]-h*self.expand_stopped_bbox-leftover_fromtop), 0)
            bbox[1] = min(int(bbox[1]+h*self.expand_stopped_bbox+leftover_frombottom), self._viewport.height)
        return bbox

    def update_from_scroll(self, *largs):
        super(StableScrollView, self).update_from_scroll(*largs)
        sh = self._viewport.height - self.height
        yvalue = -self.scroll_y*float(sh)
        if self.effect_y.value != yvalue:
            # this will automatically set self.effect_y.scroll
            self.effect_y.value = yvalue
            # now we should update the viewable window
            self.update_viewable_window()

    def update_viewable_window(self):
        vp = self._viewport
        if not vp or not self.effect_y:
            return
        sh = vp.height - self.height
        if sh < 1:
            return

        sy = -self.effect_y.scroll / float(sh)

        bbox = self._get_pure_viewbox()
        # call back once we are inside the window, for the next callback we need to get out of the window
        if self.hit_top_threshold is not None:
            self.dispatch_border_event('on_hit_top',
                                       bbox, self.hit_top_threshold*self.height)
        if self.hit_bottom_threshold is not None:
            self.dispatch_border_event('on_hit_bottom',
                                       bbox, self.hit_bottom_threshold*self.height)

        if self.border_event_dispatched['on_hit_bottom'] and not self.border_event_fired['on_hit_bottom'] :
            if not self.effect_y.is_manual and (abs(self.effect_y.velocity) < self.min_stop_velocity or abs(sy) < 0.0):
                self.dispatch('on_hit_bottom', sy)
                self.border_event_fired['on_hit_bottom'] = True

        if self.border_event_dispatched['on_hit_top'] and not self.border_event_fired['on_hit_top']:
            if not self.effect_y.is_manual and (abs(self.effect_y.velocity) < self.min_stop_velocity or abs(sy) > 1.0):
                self.dispatch('on_hit_top', sy)
                self.border_event_fired['on_hit_top'] = True

        # signal we stopped
        if ((not self.effect_y.is_manual and abs(self.effect_y.velocity) < self.min_stop_velocity) or \
                (self.effect_y.is_manual and abs(self.effect_y.velocity) < 1)) and \
                abs(self.prev_stop_pos-bbox[1]) > 50:
            self.prev_stop_pos = bbox[1]
            # expand bbox
            if self.expand_stopped_bbox > 0:
                bbox = self.get_viewbox()
            self.dispatch('on_stopped', *bbox)

        self.scroll_y = sy

    def _update_effect_y(self, *args):
        self.update_viewable_window()
        self._trigger_update_from_scroll()

    def on_hit_top(self, sy):
        pass

    def on_hit_bottom(self, sy):
        pass

    def on_stopped(self, topx, topy, bottomx, bottomy):
        pass

    def dispatch_border_event(self, event, bbox, T):
        if  self._viewport.height - self.height <= abs(T):
            return
        delta = 2.0
        dispatched = self.border_event_dispatched
        border_event_fired = self.border_event_fired

        overscroll_threshold = self.height*self.overscroll_event_threshold
        overscroll = 0
        if self.scroll_y > 1. and self.effect_y.value < 0:
            overscroll = self.effect_y.value + (self._viewport.height-self.height)
        elif self.scroll_y < 0. and self.effect_y.value > 0:
            overscroll = self.effect_y.value

        if event == 'on_hit_top':
            topy = self._viewport.height
            if ((bbox[1] > topy-T and not dispatched[event]) or overscroll<-overscroll_threshold) and self.effect_y.is_manual:
                dispatched[event] = True
                border_event_fired[event] = False
                #print ('Scroll Event %s' % event)
            elif bbox[1] < topy-T*delta:
                dispatched[event] = False
        elif event == 'on_hit_bottom':
            bottomy = 0
            if ((bbox[3] < bottomy+T and not dispatched[event]) or overscroll>overscroll_threshold) and self.effect_y.is_manual:
                dispatched[event] = True
                border_event_fired[event] = False
                #print ('Scroll Event %s %s' % (bbox, event))
            elif bbox[3] > bottomy+T*delta:
                dispatched[event] = False

    def _set_viewport_size(self, instance, value):
        trigger = True
        if value[1] != self.viewport_size[1]:
            if max(self.viewport_size[1], value[1]) > self.height:
                new_effect_y_min = -(value[1] - self.height)
                diff_heights = value[1]-self.viewport_size[1]
                if value[1] < self.viewport_size[1]:
                    # reduce size
                    if self.effect_y.value < 0 and self.last_remove_pos[1] >= -self.effect_y.value+self.height:
                        diff_heights = 0
                    pass
                else:
                    # increase size
                    if self.effect_y.value < 0 and self.last_addition_pos[1] < -self.effect_y.value:
                        diff_heights = 0
                    pass

                if new_effect_y_min==0:
                    self.scroll_y = 1.0
                    return
                if self.scroll_y == 1.0:
                    sy = 1
                else:
                    sy = (self.effect_y.value-diff_heights) / float(new_effect_y_min)
                    sy = max(0,min(sy,1))
                #dir = '<<<<<<<<' if value[1] < self.viewport_size[1] else '>>>>>>>'
                #print '%s %s = %s %s %s -- %s %s' % (dir, self.scroll_y, self.effect_y.value, self.effect_y.min, self.effect_y.max, sy * new_effect_y_min, sy)
                if sy > 0:
                    self.scroll_y = sy
                    self.effect_y.velocity = 0
                    # clear the bottom triggers - so we could get there again
                    self.border_event_fired['on_hit_bottom'] = False
                    self.border_event_dispatched['on_hit_bottom'] = False
                    # do not trigger _trigger_update_from_scroll if our scrollview is bigger than height,
                    # if we are going to be smaller than trigger.
                    trigger = not (value[1] > self.height)
            else:
                # we assume we start with empty view - so don't call hit_top until we leave it
                self.border_event_fired['on_hit_top'] = True
                self.border_event_dispatched['on_hit_top'] = True
                self.scroll_y = 1.0
                self.effect_y.velocity = 0
                #self.effect_y.reset(1.0)

        self.viewport_size = value
        # trigger manually (since we removed the binding)
        if trigger :
            self._trigger_update_from_scroll()

    def add_widget(self, widget, index=0):
        if self._viewport:
            raise Exception('ScrollView accept only one widget')
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super(ScrollView, self).add_widget(widget, index)
        self.canvas = canvas
        self._viewport = widget
        # do not! trigger on size change -
        # only after we fixed the scroll position, we call it manually.
        #widget.bind(size=self._trigger_update_from_scroll)
        self._trigger_update_from_scroll()
        widget.scrollview = self

    def update_container_add(self, widget):
        self.last_addition_pos = widget.pos

    def update_container_remove(self, widget):
        self.last_remove_pos = widget.pos

    # support for swipe
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            touch.ud[self._get_uid('svavoid')] = True
            return
        if self.disabled:
            return True
        if self._touch or (not (self.do_scroll_x or self.do_scroll_y)):
            touch.scroll = False
            return self.simulate_touch_down(touch)

        # handle mouse scrolling, only if the viewport size is bigger than the
        # scrollview size, and if the user allowed to do it
        vp = self._viewport
        scroll_type = self.scroll_type
        ud = touch.ud
        scroll_bar = 'bars' in scroll_type

        # check if touch is in bar_x(horizontal) or bay_y(bertical)
        ud['in_bar_x'] = ud['in_bar_y'] = False
        width_scrollable = vp.width > self.width
        height_scrollable = vp.height > self.height
        bar_pos_x = self.bar_pos_x[0]
        bar_pos_y = self.bar_pos_y[0]

        d = {'b': True if touch.y < self.y + self.bar_width else False,
             't': True if touch.y > self.top - self.bar_width else False,
             'l': True if touch.x < self.x + self.bar_width else False,
             'r': True if touch.x > self.right - self.bar_width else False}
        if scroll_bar:
            if (width_scrollable and d[bar_pos_x]):
                ud['in_bar_x'] = True
            if (height_scrollable and d[bar_pos_y]):
                ud['in_bar_y'] = True

        if vp and 'button' in touch.profile and \
                touch.button.startswith('scroll'):
            btn = touch.button
            m = sp(self.scroll_wheel_distance)
            e = None

            if (self.effect_x and self.do_scroll_y and height_scrollable
                    and btn in ('scrolldown', 'scrollup')):
                e = self.effect_x if ud['in_bar_x'] else self.effect_y

            elif (self.effect_y and self.do_scroll_x and width_scrollable
                    and btn in ('scrollleft', 'scrollright')):
                e = self.effect_y if ud['in_bar_y'] else self.effect_x

            if e:
                if btn in ('scrolldown', 'scrollleft'):
                    e.value = max(e.value - m, e.min)
                    e.velocity = 0
                elif btn in ('scrollup', 'scrollright'):
                    e.value = min(e.value + m, e.max)
                    e.velocity = 0
                touch.ud[self._get_uid('svavoid')] = True
                e.trigger_velocity_update()
                return True

        # no mouse scrolling, so the user is going to drag the scrollview with
        # this touch.
        self._touch = touch
        uid = self._get_uid()
        touch.grab(self)

        #print 'BUTTON DOWN %s' % str(touch.pos)

        ud[uid] = {
            'mode': 'unknown',
            'dx': 0,
            'dy': 0,
            'user_stopped': False,
            'frames': Clock.frames_displayed,
            'time': touch.time_start}

        if self.do_scroll_x and self.effect_x and not ud['in_bar_x']:
            if self.effect_x.is_manual or not self.effect_x.history or abs(self.effect_x.velocity)<1:
                self.effect_x.start(touch.x)
            else:
                self.effect_x.history = self.effect_x.history[1:] + [(time(), touch.x)]

        if self.do_scroll_y and self.effect_y and not ud['in_bar_y']:
            if not self.effect_y.history:
                self.effect_y.is_manual = True
            else:
                self.effect_y.history = self.effect_y.history[1:] + [(time(), touch.y)]
            velocity_y = self.velocity_y()
            if self.effect_y.is_manual or abs(self.effect_y.velocity) <= self.effect_y.min_velocity or \
                            abs(velocity_y) < 1:
                #print 'STARTYING YYYYY %s %s' % (self.effect_y.is_manual, velocity_y)
                self.effect_y.history = []
                self.effect_y.start(touch.y)
                self.effect_y.is_manual = True
            else:
                #print 'CONTINUE YYYYY %s %s %s' % (self.effect_y.is_manual, velocity_y, self.effect_y.history)
                self.effect_y.is_manual = True
                self.effect_y.history = [self.effect_y.history[-1]]
                if velocity_y > 50:
                    ud[uid]['user_stopped'] = True

        if (ud.get('in_bar_x', False) or ud.get('in_bar_y', False)):
            return
        if scroll_type == ['bars']:
            # touch is in parent, but _change_touch_mode expects window coords
            touch.push()
            touch.apply_transform_2d(self.to_local)
            touch.apply_transform_2d(self.to_window)
            self._change_touch_mode()
            touch.pop()
            return False
        else:
            Clock.schedule_once(self._change_touch_mode,
                                self.scroll_timeout / 1000.)
        return True

    # support for swipe
    def on_touch_move(self, touch):
        if self._get_uid('svavoid') in touch.ud:
            return
        if self._touch is not touch:
            # touch is in parent
            touch.push()
            touch.apply_transform_2d(self.to_widget)
            touch.apply_transform_2d(self.to_parent)
            touch.apply_transform_2d(self.to_local)
            super(ScrollView, self).on_touch_move(touch)
            touch.pop()
            return self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True

        uid = self._get_uid()
        ud = touch.ud[uid]
        mode = ud['mode']

        # check if the minimum distance has been travelled
        if mode == 'unknown' or mode == 'scroll':
            if self.do_scroll_x and self.effect_x:
                width = self.width
                if touch.ud.get('in_bar_x', False):
                    dx = touch.dx / float(width - width * self.hbar[1])
                    self.scroll_x = min(max(self.scroll_x + dx, 0.), 1.)
                    self._trigger_update_from_scroll()
                else:
                    if self.scroll_type != ['bars']:
                        self.effect_x.update(touch.x)
            if self.do_scroll_y and self.effect_y:
                height = self.height
                if touch.ud.get('in_bar_y', False):
                    dy = touch.dy / float(height - height * self.vbar[1])
                    self.scroll_y = min(max(self.scroll_y + dy, 0.), 1.)
                    self._trigger_update_from_scroll()
                else:
                    if self.scroll_type != ['bars']:
                        self.effect_y.update(touch.y)

        ud['dx'] += ( touch.dx )
        ud['dy'] += ( touch.dy )
        diff_frames = Clock.frames_displayed - ud['frames']
        #print '. %s %s' % (ud['dx'], ud['dy'])
        if mode == 'unknown':
            if abs(ud['dx']) > self.scroll_distance:
                #print 'SCROLL X'
                if not self.do_scroll_x and abs(ud['dx']) > 3*self.scroll_distance and diff_frames > 1:
                    # touch is in parent, but _change expects window coords
                    touch.ungrab(self)
                    self._touch = None
                    touch.push()
                    touch.apply_transform_2d(self.to_widget)
                    touch.apply_transform_2d(self.to_parent)
                    touch.scroll = True
                    ret = self.simulate_touch_down(touch)
                    touch.pop()
                    if not ret:
                        touch.grab(self)
                        self._touch = touch
                    else:
                        ud['mode'] = 'unknown'
                        return ret
                    mode = 'scroll'
                elif self.do_scroll_x:
                    mode = 'scroll'

            if abs( ud['dy'] ) > self.scroll_distance:
                #print 'SCROLL Y'
                if not self.do_scroll_y and abs( ud['dy'] ) > 3*self.scroll_distance and diff_frames > 1:
                    # touch is in parent, but _change expects window coords
                    touch.ungrab(self)
                    self._touch = None
                    touch.push()
                    touch.apply_transform_2d(self.to_widget)
                    touch.apply_transform_2d(self.to_parent)
                    touch.scroll = True
                    ret = self.simulate_touch_down(touch)
                    touch.pop()
                    if not ret:
                        touch.grab(self)
                        self._touch = touch
                    else:
                        ud['mode'] = 'unknown'
                        return ret
                    mode = 'scroll'
                elif self.do_scroll_y:
                    mode = 'scroll'
            ud['mode'] = mode

        if mode == 'scroll':

            ud['dt'] = touch.time_update - ud['time']
            ud['time'] = touch.time_update
            #ud['user_stopped'] = True
            #print '. %s %s %s' % (self.effect_y.is_manual, abs(ud['dx']), ud['user_stopped'])

            # Not sure we actually need it...
            #print 'SCROLL %s %s %s %s' % (ud['dx'], self.effect_y.is_manual, self.velocity_y(), self.effect_y.history)
            velocity_y = self.velocity_y()
            if not self.do_scroll_x and \
                    ((self.effect_y.is_manual and abs(velocity_y)<50) or abs(velocity_y)<1 ) and\
                   abs( ud['dx'] ) > 3*self.scroll_distance: #abs(ud['dx']) > 6*self.scroll_distance:
                #or abs(self.effect_y.velocity) < 1) and
                # touch is in parent, but _change expects window coords
                #print 'SCROLL HORIZONTAL %s %s %s %s' % (str(touch.pos), self.effect_y.is_manual, self.velocity_y(), self.effect_y.history)
                touch.ungrab(self)
                self._touch = None
                touch.push()
                touch.apply_transform_2d(self.to_widget)
                touch.apply_transform_2d(self.to_parent)
                touch.scroll = True
                ret = self.simulate_touch_down(touch)
                if not ret:
                    touch.pop()
                    touch.grab(self)
                    touch.scroll = False
                    self._touch = touch
                else:
                    ud['mode'] = 'unknown'
                    return ret
        return True

    def _change_touch_mode(self, *largs):
        if not self._touch:
            return False
        uid = self._get_uid()
        touch = self._touch
        ud = touch.ud[uid]
        #print 'CHANGE MODE -- %s %s' % (ud['mode'], ud['user_stopped'])
        if ud['mode'] != 'unknown' or ud['user_stopped']:
            return False
        diff_frames = Clock.frames_displayed - ud['frames']
        diff_time = time() - ud['time']

        #print 'CHANGE MOD %s frames %s' % (diff_frames,str(diff_time))

        # in order to be able to scroll on very slow devices, let at least 3
        # frames displayed to accumulate some velocity. And then, change the
        # touch mode. Otherwise, we might never be able to compute velocity, and
        # no way to scroll it. See #1464 and #1499
        if diff_time < 0.150 or diff_frames < 2: ##3
            #print 'SCHEDULE'
            Clock.schedule_once(self._change_touch_mode, 0)
            return None

        #print 'TIME %s -- %s %s %s' % (str(diff_time), self.effect_y.is_manual, [touch.dx, touch.dy], self.effect_y.history)

        if max(abs(touch.dx), abs(touch.dy)) > 2:
            #print 'SCHEDULE Dt'
            #Clock.schedule_once(self._change_touch_mode, 0)
            ud['user_stopped'] = True
            return None

        if not self.effect_y.is_manual or abs(self.velocity_y()) > self.min_stop_velocity:
            #print 'User stopped?!'
            ud['user_stopped'] = True

        if self.do_scroll_x and self.effect_x:
            if not self.effect_x.is_manual:
                #print 'User stopped x'
                ud['user_stopped'] = True
            self.effect_x.start(touch.x)
            self.effect_x.cancel()
        if self.do_scroll_y and self.effect_y:
            if not self.effect_y.is_manual:
                #print 'User stopped y'
                ud['user_stopped'] = True
            self.effect_y.start(touch.y)
            self.effect_y.cancel()

        if ud['user_stopped']:
            return None

        # XXX the next line was in the condition. But this stop
        # the possibily to "drag" an object out of the scrollview in the
        # non-used direction: if you have an horizontal scrollview, a
        # vertical gesture will not "stop" the scroll view to look for an
        # horizontal gesture, until the timeout is done.
        # and touch.dx + touch.dy == 0:
        touch.ungrab(self)
        self._touch = None
        # touch is in window coords
        touch.push()
        #touch.pos = [touch.pos[0]-ud['dx'], touch.pos[1]-ud['dy']]
        touch.apply_transform_2d(self.to_widget)
        touch.apply_transform_2d(self.to_parent)
        touch.scroll = False
        ret = self.simulate_touch_down(touch)
        if not ret:
            touch.scroll = True
            touch.pop()
            touch.grab(self)
            self._touch = touch
        else:
            touch.pop()
        return ret

    def velocity_y(self):
        if not self.effect_y or not self.effect_y.history:
            return 0

        if len(self.effect_y.history) < 2:
            return 0

        prev = self.effect_y.history[-2]
        cur = self.effect_y.history[-1]
        difft = cur[0]-prev[0]
        avg0 = (cur[1]-prev[1])/(difft+0.0000001)
        if difft > 1.5:
            #print 'Velocity timeout %s' % (difft)
            avg0 = 0
        if difft > 2.0 or len(self.effect_y.history) < 3:
            return avg0
        prev = self.effect_y.history[-3]
        cur = self.effect_y.history[-2]
        difft = cur[0]-prev[0]
        avg1 = (cur[1]-prev[1])/(difft+0.0000001)
        if difft > 1.0:
            #print 'Velocity1 timeout %s' % (difft)
            avg1 = 0
        return (avg0+avg1)/2.

    def on_touch_up(self, touch):
        if self._get_uid('svavoid') in touch.ud:
            return

        self._update_effect_y(touch)

        if self in [x() for x in touch.grab_list]:
            touch.ungrab(self)
            self._touch = None
            uid = self._get_uid()
            ud = touch.ud[uid]
            velocity_y = self.velocity_y()
            velocity = max(abs(self.effect_y.velocity), abs(velocity_y))
            is_manual = self.effect_y.is_manual or self.effect_x.is_manual
            #print 'UPPP %s %s %s' % (ud['mode'], is_manual, velocity)
            if self.do_scroll_x and self.effect_x:
                if not touch.ud.get('in_bar_x', False) and\
                        self.scroll_type != ['bars']:
                    self.effect_x.stop(touch.x)
            if self.do_scroll_y and self.effect_y and\
                    self.scroll_type != ['bars']:
                if not touch.ud.get('in_bar_y', False):
                    self.effect_y.stop(touch.y)
                    if ud['mode'] != 'scroll':
                        #print 'V after Stop %s -- %s' % (velocity_y, str(self.effect_y.history))
                        if abs(velocity_y) < 200:
                            overscroll = True
                            if self.scroll_y>=0 and self.scroll_y<=1:
                                self.effect_y.is_manual = True
                                overscroll = False
                            self._update_effect_y()
                            bbox = self.get_viewbox()
                            self.dispatch('on_stopped', *bbox)
                            if abs(ud['dy']) > self.scroll_distance/5. and (abs(velocity_y) > 50 or overscroll):
                                ud['user_stopped'] = True
                            #print 'V cancel %s -- %s' % (self.scroll_distance/5., str(ud))
                        else:
                            ud['user_stopped'] = True
            if ud['mode'] == 'unknown':
                # we must do the click at least..
                # only send the click if it was not a click to stop
                # autoscrolling
                if not ud['user_stopped']:# and max(abs(ud['dx']), abs(ud['dy'])) <= int(_scale_to_theme_dpi(5*1.333)):
                    touch.push()
                    touch.apply_transform_2d(self.to_widget)
                    touch.apply_transform_2d(self.to_parent)
                    touch.scroll = False
                    self.simulate_touch_down(touch)
                    self.effect_y.is_manual = True

            Clock.unschedule(self._update_effect_bounds)
            Clock.schedule_once(self._update_effect_bounds)
        else:
            if self._touch is not touch and self.uid not in touch.ud:
                # touch is in parents
                touch.push()
                touch.apply_transform_2d(self.to_local)
                super(ScrollView, self).on_touch_up(touch)
                touch.pop()

        # if we do mouse scrolling, always accept it
        if 'button' in touch.profile and touch.button.startswith('scroll'):
            return True

        return self._get_uid() in touch.ud