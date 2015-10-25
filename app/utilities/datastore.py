
from kivy.logger import Logger
from kivy.utils import platform

import cPickle as pickle
from os.path import isfile

from threading import RLock
from copy import deepcopy

print 'DATASTORE %s' % platform

DATAFILE_PERSISTENT_MASK = 'data/{}.ds.persistence' if platform == 'android' else \
    ('~/Documents/{}.ds.persistence' if platform == 'ios' else '../test/{}.ds.persistence')
DATAFILE_MASK = 'data/{}.ds' if platform == 'android' else \
    ('~/Documents/{}.ds' if platform == 'ios' else '../test/{}.ds')


_datastores = {}


def _make_filename(key, persistent):
    from os.path import expanduser
    if persistent:
        return expanduser(DATAFILE_PERSISTENT_MASK.format(key))
    return expanduser(DATAFILE_MASK.format(key))


def get_datastore(key, datatype=None, persistent=False):
    global _datastores
    if key in _datastores:
        ds = _datastores[key]
        if datatype and ds.datatype != datatype:
            raise Exception('datastore `{}` already exists but with a different type ({} vs {})'.format(
                key, datatype, ds.datatype))
        return ds
    filename = _make_filename(key, persistent)
    _datastores[key] = ds = Datastore(filename, datatype)
    return ds


class Datastore(object):
    _data = None
    filename = None
    datatype = list
    lock = None

    def __init__(self, filename, datatype=None):
        super(Datastore, self).__init__()
        Logger.info('Datastore: creating `%s` with type=%s' % (filename, datatype))
        self.lock = RLock()
        self.filename = filename
        if datatype:
            self.datatype = datatype
        self._data = self.datatype()
        self.load()

    def clear(self, save=True):
        self._data = self.datatype()
        if save:
            self.save()

    def save(self):
        if not self.filename:
            return
        ''' Pickle all data '''
        fn = self.filename
        try:
            with self.lock:
                with open(fn, 'wb') as f:
                    pickle.dump(self._data, f)
        except Exception as e:
            Logger.warning('Datastore: failed to save %s: %s' % (fn, e))

    def data(self, copy=True):
        with self.lock:
            if copy:
                return deepcopy(self._data)
            return self._data

    def query(self, func):
        with self.lock:
            return func(self._data)

    def update(self, arg, save=True):
        with self.lock:
            if callable(arg):
                arg(self._data)
            else:
                self._data = arg

            if save:
                self.save()

    def apply(self, func):
        ''' Apply func on each item '''
        with self.lock:
            for item in self._data:
                if func(item):
                    return True
        return False

    def load(self):
        if not self.filename:
            return
        ''' Unpickle all data '''
        fn = self.filename
        try:
            with self.lock:
                if isfile(fn):
                    with open(fn, 'rb') as f:
                        self._data = pickle.load(f)
                else:
                    Logger.warning('Datastore: can\'t load %s' % fn)
        except Exception as e:
            Logger.warning('Datastore: failed to load %s: %s' % (fn, e))
