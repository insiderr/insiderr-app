from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ListProperty
from kivy.uix.image import Image
from kivy.loader import Loader
from modules.image.img_opencv import ALoaderOpenCV


class MyImage(Image):
    cb = None
    cb_args = None
    Loaded = False

    def SetLoadCallback(self, callback, callbackargs):
        self.cb = callback
        self.cb_args = callbackargs
        if self.Loaded and self.cb:
            self.cb(self, self.cb_args)

    def Callback(self):
        self.Loaded = True
        if self.cb:
            self.cb(self, self.cb_args)


class PostBackground(FloatLayout):
    image_widget = ObjectProperty()
    image = StringProperty('')
    color = ListProperty([])

    def on_image(self, *l):
        if self.image:
            def _image_loaded(proxyImage):
                if self.image_widget:
                    if proxyImage.image and proxyImage.image.texture:
                        self.image_widget.texture = proxyImage.image.texture
                        self.image_widget.Callback()
                    else:
                        print 'NO TEXTURE %s' % self.image
            proxyImage = ALoaderOpenCV.image(self.image)
            if proxyImage.image and proxyImage.image.texture and proxyImage.image.filename == self.image:
                _image_loaded(proxyImage)
            else:
                proxyImage.bind(on_load=_image_loaded)
        else:
            self.image_widget.Loaded = False

    def clear_widget(self):
        if self.image_widget:
            self.image_widget.SetLoadCallback(None, None)
            if self.image_widget.source and not self.image_widget.Loaded:
                print 'UserPostTemplate: we should not have been here -- disposing before image loaded -- %s' % self.image_widget.source
            #self.image_widget.source = ''
        self.color = []
        self.image = ''