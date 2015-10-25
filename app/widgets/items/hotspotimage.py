from behaviors.hotspotbehavior import HotSpotBehavior
from kivy.uix.image import Image
from kivy.logger import Logger


class HotSpotImage(HotSpotBehavior, Image):
    def __init__(self, **kwargs):
        super(HotSpotImage, self).__init__(**kwargs)

    def assign(self, post):
        assert isinstance(post, self.__class__)
        self.texture = post.texture
