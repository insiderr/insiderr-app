from kivy.properties import StringProperty
from utilities.itemfactory import Item as FactoryItem
from behaviors.hotspotbehavior import HotSpotCallback, HotSpotBehavior
from kivy.logger import Logger


class TemplateItem(FactoryItem):
    key = StringProperty()

    ''' Returns a list of (name, rect) for all hotspots in this template.
        The returned list is later used by the lightweight class when calling attach_hotspots()
        NOTE: order is important!
    '''
    def get_hotspots(self):
        pass

    def make_hotspot(self, key):
        attr = getattr(self, key, None)
        if attr:
            return HotSpotBehavior.make_hotspot_description(
                key,
                attr.pos + attr.size)

    def collect_hotspots(self, callback_cls):
        hotspots = [self.make_hotspot(k) for k in callback_cls.get_hotspot_keys()]
        return [hs for hs in hotspots if hs]


class ItemCallback(HotSpotCallback):
    def item_click(self, item, touch):
        Logger.info('ItemCallback: item_click clicked for %s (not implemented)' % getattr(item, 'key', '<no key>'))

    def item_like(self, item, touch):
        Logger.info('ItemCallback: item_like clicked for %s (not implemented)' % getattr(item, 'key', '<no key>'))

    def item_dislike(self, item, touch):
        Logger.info('ItemCallback: item_dislike clicked for %s (not implemented)' % getattr(item, 'key', '<no key>'))

    def item_share(self, item, touch):
        Logger.info('ItemCallback: item_share clicked for %s (not implemented)' % getattr(item, 'key', '<no key>'))

    def item_options(self, item, touch):
        Logger.info('ItemCallback: item_options clicked for %s (not implemented)' % getattr(item, 'key', '<no key>'))

    def item_comments(self, item, touch):
        Logger.info('ItemCallback: item_comments clicked for %s (not implemented)' % getattr(item, 'key', '<no key>'))
