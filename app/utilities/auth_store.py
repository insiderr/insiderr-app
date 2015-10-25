from config import auth_ds, base_url
from urlparse import urlparse


url_key = urlparse(base_url).hostname


def store_keys():
    auth_ds.save()


def update_keys(pair, key=None):
    key = key or url_key
    def update(ds):
        d = {'priv_key': pair[0], 'pub_key': pair[1]}
        if key in ds:
            ds[key].update(d)
        else:
            ds[key] = d
    auth_ds.update(update)


def load_keys():
    try:
        def query(ds):
            if url_key in ds:
                d = ds[url_key]
                return (d.get('priv_key', None), d.get('pub_key', None))
        return auth_ds.query(query)
    except Exception:
        return None


def clear_keys():
    try:
        def update(ds):
            if url_key in ds:
                d = ds[url_key]
                for k in ('priv_key', 'pub_key'):
                    if k in d:
                        del d[k]
        return auth_ds.update(update)
    except Exception:
        return None


def store_uid(uid, key=None):
    key = key or url_key
    def update(ds):
        d = {'uid': uid}
        if key in ds:
            ds[key].update(d)
        else:
            ds[key] = d
    auth_ds.update(update)


def clear_uid():
    try:
        def update(ds):
            if url_key in ds:
                d = ds[url_key]
                if 'uid' in d:
                    del d['uid']
        return auth_ds.update(update)
    except Exception:
        return None


def load_uid():
    try:
        def query(ds):
            if url_key in ds:
                return ds[url_key].get('uid', None)
        return auth_ds.query(query)
    except Exception:
        return None



def handle_legacy():
    from functools import partial
    uid = auth_ds.query(lambda ds: ds.get('uid', None))
    priv_key = auth_ds.query(lambda ds: ds.get('priv_key', None))
    pub_key = auth_ds.query(lambda ds: ds.get('pub_key', None))
    def remove(ds, what):
        for w in what:
            del ds[w]
    if priv_key and pub_key:
        update_keys((priv_key, pub_key), key='insiderr.com')
        auth_ds.update(partial(remove, what=['priv_key', 'pub_key']))
    if uid:
        store_uid(uid, key='insiderr.com')
        auth_ds.update(partial(remove, what=['uid']))
