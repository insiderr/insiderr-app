from kivy.logger import Logger
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.graphics import RenderContext, Rectangle, BindTexture

from utilities.screenshot import screenshot_texture
from widgets.stablescrollview import StableScrollView
from widgets.items.hotspotimage import HotSpotImage

from kivy.uix.widget import Widget
from kivy.graphics.transformation import Matrix
from kivy.graphics.context_instructions import LoadIdentity
from theme import _scale_to_theme_dpi


staticplaceholdertexture = Image(source='data/placeholder.png')

FADE_TRANSITION_FS = '''$HEADER$
    uniform float t;
    uniform sampler2D tex_in;
    uniform sampler2D tex_out;

    void main(void) {
        vec4 cin = vec4(texture2D(tex_in, vec2(tex_coord0.s, 1.0 - tex_coord0.t)));
        vec4 cout = vec4(texture2D(tex_out, tex_coord0.st));
        vec4 frag_col = vec4(t * cin) + vec4((1.0 - t) * cout);
        gl_FragColor = frag_col;
    }
    '''


class ApproveWidget(Widget):
    transform = None

    def __init__(self, **kwargs):
        super(ApproveWidget, self).__init__(**kwargs)
        self.imageP = Image(
            pos=self.pos,
            size_hint=(1, 1),
            opacity = 0,
            source='data/like_animation.png')
        self.imageN = Image(
            pos=self.pos,
            size_hint=(1, 1),
            opacity = 0,
            source='data/dislike_animation.png')
        self.add_widget(self.imageP)
        self.add_widget(self.imageN)
        from kivy.graphics.context_instructions import PushMatrix, PopMatrix, MatrixInstruction
        self.transform = MatrixInstruction()
        self.canvas.before.add(PushMatrix())
        self.canvas.before.add(self.transform)
        self.canvas.after.add(PopMatrix())

    def clear(self, pos):
        self.imageP.opacity = 0
        self.imageN.opacity = 0
        self.transform.matrix = self.transform.matrix.identity()
        self.pos = pos
        self.imageP.pos = pos
        self.imageN.pos = pos

    def apply_transform(self, rescale, anchor=(0, 0)):
        trans = Matrix().scale(rescale, rescale, rescale)
        t = Matrix().translate(anchor[0], anchor[1], 0)
        t = t.multiply(trans)
        t = t.multiply(Matrix().translate(-anchor[0], -anchor[1], 0))
        self.transform.matrix = t

    def setscale(self, scale, sign):
        if sign == 0:
            sign = -1 if (scale < 0) else +1

        if sign > 0:
            self.imageP.opacity = abs(scale)
            self.imageN.opacity = 0
        else:
            self.imageN.opacity = abs(scale)
            self.imageP.opacity = 0


global_vote_widget = ApproveWidget(size_hint=(None, None),
                                   size=(100, 100),
                                   pos=(0, 0))


class Placeholder(HotSpotImage):
    def __init__(self, data, factor, target, **kwargs):
        super(Placeholder, self).__init__(
            allow_stretch=True,
            keep_ratio=False,
            **kwargs)

        self.source = None
        self.holder = None
        self.data = data
        self.factor = factor
        self.target = target
        self.staticplaceholdertexture = kwargs.get('placeholder_texture', staticplaceholdertexture.texture)
        self.texture = self.staticplaceholdertexture
        self._capturing = False
        self._anim = None
        self._cntx = None
        self._cntx_rect = None
        self.newtexture = None
        self._gesture_target = kwargs.get('gesture_target', None)
        self._gesture_anim_max_height = kwargs.get('gesture_anim_height', self.staticplaceholdertexture.height*0.6)
        self._vote_widget = None
        self._vote_scale = 0

    def dispose_widget(self):
        # make sure we are not marked as capturing, no matter where we are
        self._capturing = False

        # if we have a holder - dispose of the actual texture and switch to holder texture
        if self.holder:
            if self._anim:
                self.anim_on_complete(1)
            self.texture = self.staticplaceholdertexture
            self.holder = None
            self.newtexture = None
            self.clear_hotspots()
            self.canvas.ask_update()
            return True

        return False

    def anim_on_progress(self, *l):
        if not self._anim or not self._cntx:
            Logger.info('Placeholder: animation without ctx')
            return
        progress = l[-1]
        #Logger.info('ANIMATION %s -- %s' % (str(self), progress))
        self._cntx_rect.pos  = self.to_window(self.x, self.y)
        self._cntx['t'] = progress

    # callback to update the fadein texture position, jist before we render
    def _cntx_callback(self, *largs):
        self._cntx_rect.pos  = self.to_window(self.x, self.y)

    def anim_on_complete(self, *l):
        #Logger.info('ANIMATION %s -- complete' % (str(self)))
        if self._anim:
            self._anim.cancel(self)
            self._anim = None

        if self._cntx:
            self.canvas.remove(self._cntx)

        # updating the texture actually triggers screen update
        # so do it after you removed the animation context
        if self.newtexture:
            self.texture = self.newtexture
            self.newtexture = None
            self._cntx = None
            self._cntx_rect = None
            # hotspots should have been cleared, if they are not, don't mess it up
            self.attach_hotspots(self.target, self._hotspots, clear=False)

    def assign(self, widget, scrollview_container=None):
        if self._anim:
            Logger.info('Placeholder: assign with animation')
            return
        # first update our size to the new texture size.
        self.size = self.newtexture.size
        self.texture_size = self.newtexture.size

        self._hotspots = widget.get_hotspots()

        visual_bbox = None
        if scrollview_container:
            visual_bbox = StableScrollView.BBox(*scrollview_container._get_pure_viewbox())
        if not visual_bbox or not self.collide_widget(visual_bbox):
            self.anim_on_complete(1.0)
        else:
            self._cntx = RenderContext(use_parent_projection=True)
            self._cntx.shader.fs = FADE_TRANSITION_FS
            with self._cntx:
                # here, we are binding a custom texture at index 1
                # this will be used as texture1 in shader.
                BindTexture(texture=self.newtexture, index=1)

                # create a rectangle with texture (will be at index 0)
                pos = self.to_window(self.x, self.y)
                self._cntx_rect = Rectangle(size=self.size, pos=pos, texture=self.holder, tex_coords=self.holder.tex_coords)

                # callback to update position
                #Callback(self._cntx_callback)

            # set the texture1 to use texture index 1
            self._cntx['t'] = 0.0
            self._cntx['tex_in'] = 1
            self._cntx['tex_out'] = 0
            self.canvas.add(self._cntx)

            # set the animation in progress
            self._anim = Animation(duration=0.250, s=0)
            self._anim.bind(on_progress=self.anim_on_progress,
                            on_complete=self.anim_on_complete)
            self._anim.start(self)

    def _capture_widget(self, instance, largs):
        widget, = largs
        scrollview_container = widget.scrollview_container
        def update_tex(tex):
            if not self.holder:
                self.holder = self.texture
            #else:
            #    Logger.info('Placeholder: update_text when we already have one %s' % self.data)
            self.newtexture = tex
            # mark end of capturing process
            self._capturing = False
            # start animation and stuff
            self.assign(widget, scrollview_container)

        # we actually should wait another frame to make sure the frame is rendered
        def capture_add_texture(dt):
            screenshot_texture(widget, update_tex)
            widget.dispose()

        Clock.schedule_once(capture_add_texture, 0.025)

    def _update_data(self, data):
        # update data, if we already have data - only update the fields we already have
        data_updated = False
        if isinstance(data, dict):
            if self.data:
                for k in set(data.keys()).intersection(self.data.keys()):
                    if self.data[k] != data[k]:
                        data_updated = True
                        self.data[k] = data[k]
            else:
                data_updated = True
                self.data = data
        return data_updated

    def update_widget(self, data=None, ignore_old_data=False, **kwargs):
        # if we already have a texture or we are already capturing
        if (self.holder or self._capturing) and (not data or self.data == data):
            return False

        if ignore_old_data:
            self.data = data
            data_updated = True
        else:
            data_updated = self._update_data(data)

        # if we already have a texture and nothing was changed, skip it.
        if self.holder and not data_updated:
            return False

        # mark us as already capturing,
        # so we shouldn't schedule another call while we are waiting to capture.
        self._capturing = True

        # create the item
        item = self.factor(self.data)
        if not item:
            # Logger.info('Placeholder: update_widget - we didnt get an item')
            # we failed creating the item, let's reschedule
            retries = kwargs.get('retries', 0)
            if retries < 3:
                from functools import partial
                Clock.schedule_once(partial(self.update_widget, retries=retries+1), 0.250)
            return True

        # schedule capture callback
        item.size_hint_x = None
        item.width = self.width
        item.scrollview_container = kwargs.get('scrollview_container', None)
        # if there is no callback just initiate the call now
        if not item.set_load_callback(self._capture_widget, item):
            self._capture_widget(item, [item])
        return True

    def update_texture(self, newtexture):
        if not self.holder:
            self.holder = self.texture
        self.texture = newtexture

    def update_widget_data(self, data, retries=0, ignore_old_data=False):
        # if we don't have a texture, just update the data
        if not self.holder:
            if self.data and not ignore_old_data:
                for k in set(data.keys()).intersection(self.data.keys()):
                    self.data[k] = data[k]
            else:
                self.data = data
        else:
            # update texture
            return self.update_widget(data=data, ignore_old_data=ignore_old_data)

    def pass_touch_to_spot(self, spot):
        if spot and spot[3][2]*spot[3][3] < 100*100:
            return True
        return False

    def check_touch_gesture(self, touch):
        return True

    def on_touch_down(self, touch):
        if not self._gesture_target:
            return super(Placeholder, self).on_touch_down(touch)

        # close on double tap
        if touch.is_double_tap:
            touch.grab(self)
            touch.grab_current = self
            try:
                self.parent.parent.parent.parent.parent.dispatch('on_close')
            except:
                self.parent.parent.parent.parent.parent.parent.dispatch('on_close')
            return True

        if self.disabled or not self.collide_point(*touch.pos):
            return False

        #Logger.info('<<<DOWN>>>: %s -- pos=%s osx=%s sx=%s' % (self.data['content'], touch.pos, touch.osx, touch.sx))

        spot = self.find_hotspot_touch(touch)
        if spot and self.pass_touch_to_spot(spot):
            return super(Placeholder, self).on_touch_down(touch)

        if not self.check_touch_gesture(touch):
            return False

        cx, cy = self.to_window(*self.center)
        #print 'pos %s -- %s %s' % (self.center, cx, cy)
        window = self.get_parent_window()
        if cy < 0 or cy > window.height:
            return False


        touch.grab(self)
        touch.grab_current = self


        touch.dx = touch.dy = 0
        #touch.x, touch.y = cx, cy
        #touch.sx, touch.sy = float(touch.x)/window.width, float(touch.y)/window.height
        touch.ox, touch.oy = touch.px, touch.py = touch.pos
        touch.osx, touch.osy = touch.psx, touch.psy = touch.sx, touch.sy

        #Logger.info('<<<DOWN>>>:  -- pos=%s osx=%s sx=%s' % (touch.pos, touch.osy, touch.sy))
        if hasattr(touch, 'scroll') and touch.scroll:
            self._vote_scale = 0.001
        else:
            self._vote_scale = 0

        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        swipe_range = 0.35
        swipe_dx = touch.osx - touch.sx
        swipe_range_y = 0.35
        swipe_dy = touch.osy - touch.sy
        touch_distance = max(abs(swipe_dx), abs(swipe_dy))
        #Logger.info('<<<MOVE>>>: %s %s %s %s' % (str(touch.pos), touch_distance, touch.dx, touch.dy))
        scale = min(1, max(.001, abs(swipe_dx) / abs(swipe_range)))
        scale_y = min(1, max(.001, abs(swipe_dy) / swipe_range_y))
        sign = float(swipe_dx) / swipe_range
        self._vote_scale = scale if sign >= 0 else -scale
        if not self._vote_widget and abs(scale) > 0.1:
            cx, cy = self.to_window(*self.center)
            global global_vote_widget
            self._vote_widget = global_vote_widget
            pos = (cx - self._vote_widget.width/2, cy - self._vote_widget.height/2)
            self._vote_widget.clear(pos=pos)
            if self._gesture_target:
                self._gesture_target.add_gesture_animation(self._vote_widget)

        v = self._vote_widget
        if v:
            #Logger.info('<<<MOVE>>>: osx=%s sx=%s r=%s dx=%s' % (touch.osx, touch.sx, swipe_range, swipe_dx))
            rescale = 1+_scale_to_theme_dpi(2*1.33)*scale
            if v.height*3 > self._gesture_anim_max_height and rescale*v.height > self._gesture_anim_max_height:
                rescale = float(self._gesture_anim_max_height)/float(v.height)

            if scale_y < 0.0:
                pass
            elif scale_y > 0.35:
                scale = .001
            elif scale_y >= 0.0:
                scale *= 1. ##-scale_y
            self._vote_scale = scale if sign >= 0 else -scale
            #Logger.info('<<<MOVE>>>: %s %s osy=%s sy=%s r=%s dy=%s' % (scale, scale_y, touch.osy, touch.sy, swipe_range_y, swipe_dy))

            ancore = v.center
            #print 'anim: pos %s sign %s scaling %s ancore %s' % (v.pos, sign, scale, ancore)
            v.apply_transform(rescale=rescale, anchor=ancore)
            v.setscale(scale, sign)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        touch.grab_current = None
        swipe_dx = touch.osx - touch.sx
        swipe_dy = touch.osy - touch.sy
        touch_distance = max(abs(swipe_dx), abs(swipe_dy))
        #Logger.info('<<< UP >>>: %s %s %s %s %s' % (self._vote_scale, str(touch.pos), touch_distance, touch.dx, touch.dy))
        if self._vote_widget:
            def remove_vote_widget(*largs):
                if self._gesture_target:
                    self._gesture_target.remove_gesture_animation(self._vote_widget)
                self._vote_widget = None

            if abs(self._vote_scale) < 0.001 and touch_distance < 0.001:
                remove_vote_widget()
                self.call_on_release(touch)
            elif self._vote_scale < -0.80:
                self._vote_widget.setscale(1., self._vote_scale)
                self.target.item_gesture_right(self, touch)
                Clock.schedule_once(remove_vote_widget, 0.500)
            elif self._vote_scale > 0.80:
                self._vote_widget.setscale(1., self._vote_scale)
                self.target.item_gesture_left(self, touch)
                Clock.schedule_once(remove_vote_widget, 0.500)
            else:
                remove_vote_widget()

            self._vote_scale = 0
        else:
            if abs(self._vote_scale) < 0.0001:
                super(Placeholder, self).on_touch_down(touch)
                super(Placeholder, self).on_touch_up(touch)
            self._vote_scale = 0

        return True

