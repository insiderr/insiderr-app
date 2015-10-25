import Queue
from kivy.logger import Logger


class Item(object):
    def attach(self, queue):
        self.queue = queue

    def set_load_callback(self, cb, *args):
        return False

    def dispose(self):
        try:
            self.queue.put(self)
        except Exception as e:
            Logger.info('ItemFactory: exception %s' % str(e))
        finally:
            pass

    def update(self, data):
        pnames = set(self.properties().keys()).intersection(set(data.keys()))
        for pname in pnames:
            self.property(pname).set(self, data[pname])


class ItemFactory(object):
    def __init__(self, maxsize, item_cls):
        assert issubclass(item_cls, Item)
        self.queue = Queue.Queue(maxsize)
        self.items = list()
        self.item_cls = item_cls

    def get_item(self, data):
        if len(self.items) < self.queue.maxsize:
            item = self.item_cls(**data)
            item.attach(self.queue)
            self.items.append(item)
        else:
            try:
                item = self.queue.get_nowait()
                item.update(data)
            except Queue.Empty:
                return None
        return item