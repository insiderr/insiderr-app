from kivy.event import EventDispatcher
from functools import partial
from kivy.logger import Logger


class Stream(EventDispatcher):
    items_per_page = 10
    manager = None

    def __init__(self, manager, **kwargs):
        self.manager = manager
        self.cache = dict()
        self.hash_bounds = None
        super(Stream, self).__init__(**kwargs)

    def _validate_args(self, args, prev=False):
        # if count is not provided, use default items per page
        args['count'] = args.get('count', self.items_per_page)
        return args

    def _update_cache(self, data):
        if data:
            new_entries = dict((d['post']['key'], d) for d in data)
            new_hashes = set(d['hash'] for d in data)
            nmin, nmax = min(new_hashes), max(new_hashes)
            if not self.hash_bounds:
                self.hash_bounds = [nmin, nmax]
            else:
                cmin, cmax = self.hash_bounds
                self.hash_bounds = [ min(cmin, nmin), max(cmax, nmax) ]

            self.cache.update(new_entries)

    def _on_page(self, data, on_page, **kwargs):
        try:
            self._update_cache(data)
        except Exception as ex:
            pass
        on_page(data)

    def get_page(self, on_page, on_error=None, **kwargs):
        self._do_get_page(
            on_page=partial(self._on_page, on_page=on_page),
            on_error=on_error,
            **(self._validate_args(kwargs)))

    def get_current_page(self, on_page, on_error=None):
        self._do_get_page(
            on_page=partial(self._on_page, on_page=on_page),
            on_error=on_error,
            hash=self.hash_bounds[0] if self.hash_bounds else None,
            count=-self.items_per_page)

    def get_prev_page(self, on_page, on_error=None):
        if self.hash_bounds and self.hash_bounds[0]:
            self._do_get_page(
                on_page=partial(self._on_page, on_page=on_page),
                on_error=on_error,
                hash=self.hash_bounds[0],
                count=-self.items_per_page)

    def get_next_page(self, on_page, on_error=None):
        if self.hash_bounds and self.hash_bounds[1]:
            self._do_get_page(
                on_page=partial(self._on_page, on_page=on_page),
                on_error=on_error,
                hash=self.hash_bounds[1],
                count=self.items_per_page)

    def _do_get_page(self, on_page, on_error, **kwargs):
        pass

