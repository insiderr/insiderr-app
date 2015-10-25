
from Queue import Queue
from kivy.logger import Logger
from kivy.properties import NumericProperty
from kivy.clock import Clock

class QueueAddWidgetBehavior(object):
    __events__ = ('on_queue_empty', 'on_queue_processing')
    _queue = None
    _queued_keys = None
    _trigger_add_widget = None
    widgets_per_frame = NumericProperty(1)

    # needed for StableScrollView
    last_inserted_object_location = None

    def __init__(self, **kwargs):
        self._queue = Queue()
        self._queued_keys = set()
        self.last_inserted_object_location = 0
        triger_refresh_timer = kwargs.get('refresh_timer', 0)
        self._trigger_add_widget = Clock.create_trigger(self._do_add_widget, triger_refresh_timer)
        super(QueueAddWidgetBehavior, self).__init__(**kwargs)
        self.tics = 0.
        self.ticcnt = 0.

    # TODO: add request ID to make sure we're not turning off
    # an ongoing update because of the results of an older one
    def on_queue_empty(self):
        pass

    def on_queue_processing(self):
        pass

    def enqueue(self, key, data, index=0):
        try:
            if key in self._queued_keys:
                # Don't enqueue, it's already there
                return False
            self._queued_keys.add(key)
            self._queue.put((key, data, index))
            self._trigger_add_widget()
            return True
        except Exception as e:
            Logger.warning('QueueAddWidgetBehavior: exception on enqueue() - %s' % e)
            return False

    def _produce_widget(self, key, data):
        pass

    def _do_add_widget(self, *args):
        import time
        try:
            for i in range(self.widgets_per_frame):
                if self._queue.empty():
                    self._signal_queue_empty()
                    return
                key, data, index = self._queue.get()
                self._queued_keys.discard(key)
                tic = time.clock()
                try:
                    widget = self._produce_widget(key, data)
                except Exception as e:
                    Logger.warning('QueueAddWidgetBehavior: producer error: %s' % e)
                    continue
                if not widget:
                    # if we couldn't create object - re-trigger
                    self._queued_keys.add(key)
                    self._queue.put((key, data, index))
                    break
                self.tics += time.clock() - tic
                self.ticcnt += 1.
                # Logger.info('_do_add_widget -- ctor producer %.3f ms' % float(1000.*self.tics/self.ticcnt))
                # ctor stats - clear every 10 widgets
                if self.ticcnt > 10:
                    self.ticcnt = 0
                    self.tics = 0
                if index < 0:
                    index = len(self.children)+index+1

                self.last_inserted_object_location = index

                self._add_widget_impl(widget, index)

            self._trigger_add_widget()

        except Exception as e:
            Logger.warning('QueueAddWidgetBehavior: exception on _do_add_widget() - %s' % e)

    def _signal_queue_empty(self):
        self.dispatch('on_queue_empty')

    def _add_widget_impl(self, widget, index):
        self.add_widget(widget, index)
