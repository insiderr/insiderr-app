#-*- coding: utf-8 -*-
#
#    Blah

'''opencv wrapper'''


__all__ = ('ALoaderOpenCV', 'ImageOpenCV', 'AsyncImageOpenCV')

from kivy.logger import Logger
from kivy.core.image import ImageLoader
from kivy.compat import PY2
from os import write, close, O_RDWR, O_CREAT
from os import open as openfile
import mimetypes


from kivy.uix.image import Image as UixImage
from kivy.core.image import Image as CoreImage
from kivy.cache import Cache
from kivy.loader import LoaderThreadPool
from kivy.graphics.texture import Texture
from kivy.resources import resource_find
from kivy.properties import BooleanProperty, NumericProperty
from modules.core.crc64 import CRC64digest
from modules.core.tempstorage import get_temp_folder_prefix
from kivy.compat import queue
from threading import Thread


class _WorkerLow(Thread):
    '''Thread executing tasks from a given tasks queue
    '''
    def __init__(self, pool, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.pool = pool
        self.start()

    def run(self):
        from kivy import platform
        if platform == 'android':
            from jnius import autoclass
            AndroidSystem = autoclass('android.os.Process')
            AndroidSystem.setThreadPriority(AndroidSystem.THREAD_PRIORITY_LOWEST)
            Logger.info('_WorkerLow: set low thread property')
        while self.pool.running:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            self.tasks.task_done()


class _ThreadPoolLow(object):
    '''Pool of threads consuming tasks from a queue
    '''
    def __init__(self, num_threads):
        super(_ThreadPoolLow, self).__init__()
        self.running = True
        self.tasks = queue.Queue()
        for _ in range(num_threads):
            _WorkerLow(self, self.tasks)

    def add_task(self, func, *args, **kargs):
        '''Add a task to the queue
        '''
        self.tasks.put((func, args, kargs))

    def stop(self):
        self.running = False
        self.tasks.join()


class LoaderOpenCV(LoaderThreadPool):
    def __init__(self, **kwargs):
        super(LoaderOpenCV, self).__init__(**kwargs)

    def __del__(self):
        super(LoaderOpenCV, self).__del__()

    def _set_num_workers(self, num):
        if num < 1:
            raise Exception('Must have at least 1 workers')
        self._num_workers = num

    def _get_num_workers(self):
        return self._num_workers

    num_workers = property(_get_num_workers, _set_num_workers)

    def start(self):
        super(LoaderThreadPool, self).start()
        self.pool = _ThreadPoolLow(self._num_workers)
        from kivy.clock import Clock
        Clock.schedule_interval(self.run, 0)

    def drop_request(self, filename, client, load_callback=None, post_callback=None, **kwargs):
        #Logger.info('_drop_request: from cache queue %s %d %d' % (filename,len(self._client),len(self._q_load)))
        item = None
        for i in self._client:
            if (i[0] == filename):
                #and (i[1] == client):
                item = i
                break
        if item:
            Logger.info('_drop_request: found client %s ' % filename)
            self._client.remove(item)

        item = None
        for i in self._q_load:
            if (i['filename'] == filename):
                #and (i['load_callback'] == load_callback) and (i['post_callback'] == post_callback):
                item = i
                break
        if item:
            Logger.info('_drop_request: found _q_load %s ' % filename)
            self._q_load.remove(item)

        if not kwargs.get('nocache', False):
            #Logger.info('_drop_request: dropped %s ' % filename)
            Cache.remove('kv.loader', filename)

    def _load_local(self, filename, kwargs):
        '''(internal) Loading a local file'''
        # With recent changes to CoreImage, we must keep data otherwise,
        # we might be unable to recreate the texture afterwise.
        # -- Well we don't need it - we use opencv image
        return ImageLoader.load(filename, keep_data=True, **kwargs)

    def _load_urllib(self, filename, kwargs):
        '''(internal) Loading a network file. First download it, save it to a
        temporary file, and pass it to _load_local().'''
        if PY2:
            import urllib2 as urllib_request
        else:
            import urllib.request as urllib_request
        proto = filename.split(':', 1)[0]
        if proto == 'smb':
            try:
                # note: it's important to load SMBHandler every time
                # otherwise the data is occasionaly not loaded
                from smb.SMBHandler import SMBHandler
            except ImportError:
                Logger.warning(
                    'Loader: can not load PySMB: make sure it is installed')
                return
        _BINARY = 0
        import glob
        import tempfile
        from kivy import platform
        if platform in ['win', 'windows']:
            from os import O_BINARY
            _BINARY = O_BINARY

        data = fd = _out_osfd = None
        try:
            # check if we already have the file locally
            filename_hash = CRC64digest(filename)
            filename_hashed_no_ext = get_temp_folder_prefix()+filename_hash
            filename_hash_cached = glob.glob(filename_hashed_no_ext+'.*')
            #Logger.info('url_load: <%s> %s <%s> %s' % (filename,filename_hash,filename_hashed_no_ext,filename_hash_cached))

            data = None
            if len(filename_hash_cached) > 0:
                # load data
                Logger.info('AsyncImageOpenCV: Loading local cached <%s>' % filename_hash_cached[0])
                try:
                    data = self._load_local(filename_hash_cached[0], kwargs)
                except Exception:
                    data = None

            # try to download
            if data is None:
                Logger.info('AsyncImageOpenCV: download <%s>' % filename)
                if proto == 'smb':
                    # read from samba shares
                    fd = urllib_request.build_opener(SMBHandler).open(filename)
                else:
                    # read from internet
                    fd = urllib_request.urlopen(filename)

                idata = fd.read()
                info = fd.info()
                fd.close()
                fd = None
                if 'content-type' in info.keys():
                    suffix = mimetypes.guess_extension(info['content-type'])
                else:
                    suffix = '.%s' % (filename.split('.')[-1])

                _out_filename = filename_hashed_no_ext+suffix

                # write to local filename
                _out_osfd = openfile(_out_filename,  O_RDWR | O_CREAT | _BINARY)
                write(_out_osfd, idata)
                close(_out_osfd)
                _out_osfd = None

                # load data
                data = self._load_local(_out_filename, kwargs)

            # FIXME create a clean API for that
            for imdata in data._data:
                imdata.source = filename
        except Exception:
            Logger.exception('Failed to load image <%s>' % filename)
            # close file when remote file not found or download error
            try:
                close(_out_osfd)
                _out_osfd = None
            except OSError:
                pass
            return self.error_image
        finally:
            if fd:
                fd.close()
            if _out_osfd:
                close(_out_osfd)
            #if _out_filename != '':
            #    unlink(_out_filename)

        return data

ALoaderOpenCV = LoaderOpenCV()
#Loader = ALoaderOpenCV


class CoreImageOpenCV(CoreImage):
    res_width = NumericProperty(-1)
    res_height = NumericProperty(-1)
    res_autosize = BooleanProperty(False)
    load_exif = BooleanProperty(False)

    def __init__(self, arg, **kwargs):
        #Logger.info('CoreImageOpenCV: kwargs %s' % (kwargs))
        self.res_width = kwargs.get('res_width', -1)
        self.res_height = kwargs.get('res_height', -1)
        self.load_exif = kwargs.get('load_exif', False)
        if self.res_autosize and self.res_width <= 0:
            self.res_width = self.width
        if self.res_autosize and self.res_height <= 0:
            self.res_height = self.height
        kwargs['res_width'] = self.res_width
        kwargs['res_height'] = self.res_height
        super(CoreImageOpenCV, self).__init__(arg, **kwargs)

    def _set_filename(self, value):
        #Logger.info('CoreImageOpenCV: value %s' % (value))
        if value is None or value == self._filename:
            return
        self._filename = value

        # construct uid as a key for Cache
        if (self.res_width > 0) or (self.res_height > 0):
            uid = '%s|%d|%d|%s|%s' % (self.filename, self.res_width, self.res_height, self._mipmap, 0)
        else:
            uid = '%s|%s|%s' % (self.filename, self._mipmap, 0)

        # in case of Image have been asked with keep_data
        # check the kv.image cache instead of texture.
        image = Cache.get('kv.image', uid)
        if image:
            # we found an image, yeah ! but reset the texture now.
            self.image = image
            # if image.__class__ is core image then it's a texture
            # from atlas or other sources and has no data so skip
            if (image.__class__ != self.__class__ and
                    not image.keep_data and self._keep_data):
                self.remove_from_cache()
                self._filename = ''
                self._set_filename(value)
            else:
                self._texture = None
                self._img_iterate()
            return
        else:
            # if we already got a texture, it will be automatically reloaded.
            _texture = Cache.get('kv.texture', uid)
            if _texture:
                self._texture = _texture
                return

        # if image not already in cache then load
        tmpfilename = self._filename
        #Logger.info('CoreImageOpenCV: set_filename %s' % (tmpfilename))
        #Logger.info('CoreImageOpenCV: %d %d' % (self.res_width, self.res_height))
        image = ImageLoader.load(
            self._filename, keep_data=self._keep_data,
            mipmap=self._mipmap, nocache=self._nocache, res_width=self.res_width,
            res_height=self.res_height, load_exif=self.load_exif)
        self._filename = tmpfilename

        # put the image into the cache if needed
        if isinstance(image, Texture):
            self._texture = image
            self._size = image.size
        else:
            self.image = image
            if not self._nocache:
                Cache.append('kv.image', uid, self.image)

    def _get_filename(self):
        return self._filename

    filename = property(_get_filename, _set_filename,
                        doc='Get/set the filename of image')


class ImageOpenCV(UixImage):
    res_width = NumericProperty(-1)
    res_height = NumericProperty(-1)
    res_autosize = BooleanProperty(False)
    load_exif = BooleanProperty(False)
    auto_update_size = BooleanProperty(False)

    def __init__(self, **kwargs):

        #Logger.info('ImageOpenCV: INIT [%d %d] ' % (self.res_width,self.res_height))
        self.res_width = kwargs.get('res_width', -1)
        self.res_height = kwargs.get('res_height', -1)
        self.load_exif = kwargs.get('load_exif', False)
        self.auto_update_size = kwargs.get('auto_update_size', False)
        if self.res_autosize and self.res_width <= 0:
            self.res_width = self.width
        if self.res_autosize and self.res_height <= 0:
            self.res_height = self.height
        kwargs['res_width'] = self.res_width
        kwargs['res_height'] = self.res_height
        super(ImageOpenCV, self).__init__(**kwargs)

    def texture_update(self, *largs, **kwargs):
        #Logger.info('ImageOpenCV: texture_update %s' % kwargs)
        if not self.source:
            self.texture = None
        elif 'atlas://' in self.source:
            return super(ImageOpenCV, self).texture_update(self, *largs, **kwargs)
        else:
            filename = resource_find(self.source)
            if filename is None:
                return Logger.error('ImageOpenCV: Error reading file {filename}'.
                                    format(filename=self.source))
            mipmap = self.mipmap
            if self._coreimage is not None:
                self._coreimage.unbind(on_texture=self._on_tex_change)

            try:
                #Logger.info('ImageOpenCV: resource size [%d %d] ' % (self.res_width,self.res_height))
                kwargs['res_width'] = self.res_width
                kwargs['res_height'] = self.res_height
                #Logger.info('ImageOpenCV: kwargs %s' % kwargs)
                self._coreimage = ci = CoreImageOpenCV(filename, mipmap=mipmap,
                                                       anim_delay=self.anim_delay,
                                                       keep_data=self.keep_data,
                                                       nocache=self.nocache,
                                                       load_exif=self.load_exif,
                                                       **kwargs)
            except:
                self._coreimage = ci = None

            if ci:
                if self.auto_update_size and ci._texture:
                    self.size = [ci._texture.width, ci._texture.height]
                    self.width = ci._texture.width
                    self.height = ci._texture.height

                ci.bind(on_texture=self._on_tex_change)
                self.texture = ci.texture


class AsyncImageOpenCV(ImageOpenCV):

    def __init__(self, **kwargs):
        self.prev_source = None
        self.prev_opacity = None
        self.prev_allow_stretch = None
        self.Loaded = False
        self._LoadedCallBack = kwargs.get('LoadedCallBack', None);
        self._LoadedCallBackArgs = kwargs.get('LoadedCallBackArgs',[]);

        self._coreimage = None
        super(AsyncImageOpenCV, self).__init__(**kwargs)
        self.bind(source=self._load_source)
        if self.source:
            self._load_source()
        #Logger.info('AsyncImageOpenCV: resource size [%d %d] ' % (self.res_width,self.res_height))

    def __del__(self):
        self.unbind(source=self._load_source)
        self._coreimage.unbind(on_load=self._on_source_load)
        self._coreimage.unbind(on_texture=self._on_tex_change)
        super(AsyncImageOpenCV, self).__del__()

    def on_parent(self, instance, value):
        if value is None:
            ALoaderOpenCV.drop_request(self.source, self._coreimage)

    def on_load(self):
        self.allow_stretch = self.prev_allow_stretch
        self.prev_allow_stretch = None
        #Logger.info('_AsyncImage_load_source: on_load: ImageLoad %s ' % self.allow_stretch)
        pass

    def _load_source(self, *args, **kwargs):
        #Logger.info('_AsyncImage_load_source: %s', (self.source))
        self.Loaded = False
        if not self.prev_allow_stretch:
            self.prev_allow_stretch = self.allow_stretch
            self.allow_stretch = False
            #Logger.info('_AsyncImage_load_source: _load_source: ImageProxy %s' % self.prev_allow_stretch)

        source = self.source
        if self.prev_source:
            ALoaderOpenCV.drop_request(self.prev_source, self._coreimage)
        self.prev_source = source
        if not source:
            if self._coreimage is not None:
                self._coreimage.unbind(on_texture=self._on_tex_change)
            self.texture = None
            self._coreimage = None
            self.prev_opacity = self.opacity
            self.opacity = 0.0
        else:
            if self._coreimage:
                self._coreimage.unbind(on_load=self._on_source_load)
                self._coreimage.unbind(on_texture=self._on_tex_change)

            if not self.is_uri(source):
                source = resource_find(source)
            kwargs['res_width'] = self.res_width
            kwargs['res_height'] = self.res_height
            kwargs['load_exif'] = self.load_exif
            #Logger.info('AsyncImageOpenCV: ----- resource size [%d %d] ' % (self.res_width,self.res_height))
            self._coreimage = image = ALoaderOpenCV.image(source,
                                                          nocache=self.nocache,
                                                          mipmap=self.mipmap, **kwargs)
            image.bind(on_load=self._on_source_load)
            image.bind(on_texture=self._on_tex_change)
            self.texture = image.texture
            if self.prev_opacity:
                self.opacity = self.prev_opacity
            else:
                self.prev_opacity = self.opacity

            # if the image was loaded from cache we already have it -
            # so on load won't be called - call it manually -
            # but make sure it's not the placeholder image
            if (image.loaded is True) and (image._texture is not None):
                self._coreimage.dispatch('on_load')

    def _on_source_load(self, value):
        if self.prev_allow_stretch:
            #Logger.info('_AsyncImage_load_source: _load_source: Allow %s' % self.prev_allow_stretch)
            self.allow_stretch = self.prev_allow_stretch
            self.prev_allow_stretch = None
        #Logger.info('_AsyncImage_load_source: _load_source: %s' % self.source)
        self.Loaded = True
        image = self._coreimage.image
        if not image:
            #return
            pass
        else:
            self.texture = image.texture

        if self._LoadedCallBack:
            self._LoadedCallBack(self, self._LoadedCallBackArgs)

    def SetLoadCallback(self, cb, cbargs):
        self._LoadedCallBack = cb
        self._LoadedCallBackArgs = cbargs
        if self.Loaded and self._LoadedCallBack:
            self._LoadedCallBack(self, self._LoadedCallBackArgs)

    def is_uri(self, filename):
        proto = filename.split('://', 1)[0]
        return proto in ('http', 'https', 'ftp', 'smb')

    def _on_tex_change(self, *largs):
        if self._coreimage:
            self.texture = self._coreimage.texture

    def texture_update(self, *largs):
        pass


g_bInitialized = False

# register
if not g_bInitialized:
    from kivy import platform
    if platform in ['android', 'linux']:
        from native_opencv import ImageLoaderOpenCV
        #ImageLoader.register(ImageLoaderOpenCV)
        ImageLoader.loaders.insert(0, ImageLoaderOpenCV)
    g_bInitialized = True

#####################################################################################

