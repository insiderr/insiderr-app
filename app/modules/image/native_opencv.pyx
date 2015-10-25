#-*- coding: utf-8 -*-
#
#    Blah

'''opencv wrapper'''


__all__ = ('ImageLoaderOpenCV')

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader
from kivy.core.image import Image as ImageBase
from kivy.graphics.texture import Texture
from kivy.cache import Cache

from kivy.compat import PY2
from os import write, close, unlink, environ, O_RDWR, O_CREAT
from os import open as openfile
import mimetypes

from array import array
from libcpp cimport bool
from libcpp.string cimport string
from libcpp.vector cimport vector
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy, memset

ctypedef unsigned long size_t

cdef extern from "stdlib.h":
    void* calloc(size_t, size_t)

from cpython cimport PyString_FromStringAndSize
from cpython cimport PyString_AsString


cdef extern from "opencv2/core/core.hpp" namespace "cv":
    cdef cppclass Size_[_Tp]:
        Size_() nogil
        Size_(_Tp _width, _Tp _height) nogil
        Size_(const Size_& sz) nogil
        _Tp width, height
    ctypedef Size_[int] Size2i
    ctypedef Size2i Size

    cdef cppclass Point_[_Tp]:
        _Tp x, y
    ctypedef Point_[float] Point2f

    cdef cppclass Rect_[_Tp]:
        Rect_() nogil
        Rect_(_Tp _x, _Tp _y, _Tp _width, _Tp _height) nogil
        Rect_(const Rect_& r) nogil
        _Tp area() nogil
        _Tp x, y, width, height

    ctypedef Rect_[int] Rect

    cdef cppclass _InputArray:
        _InputArray()
        _InputArray(Mat& m)

    ctypedef _InputArray InputArray

    cdef cppclass _OutputArray(_InputArray):
        _OutputArray()
        _OutputArray(Mat& m)

    ctypedef _OutputArray OutputArray

    cdef cppclass Mat:
        Mat() nogil
        Mat(const Mat& m) nogil
        Mat(Size size, int type) nogil
        Mat(int _rows, int _cols, int _type) nogil
        Mat(int rows, int cols, int type, void* data) nogil
        Mat(const Mat& m, const Rect& roi) nogil
        void copyTo(OutputArray m) nogil
        bool isContinuous() nogil
        int type() nogil
        int channels() nogil
        void create(int rows, int cols, int type)
        void create(Size size, int type)
        size_t step1(int i) nogil
        size_t elemSize() nogil
        size_t total() nogil
        bool empty() nogil
        Mat& setTo(InputArray value, InputArray mask) nogil
        int dims, rows, cols
        unsigned char *data

    void mixChannels(const vector[Mat]& src, vector[Mat]& dst, const int* fromTo, size_t npairs) nogil
    void addWeighted(InputArray src1, double alpha, InputArray src2, double beta, double gamma,
                     OutputArray dst, int dtype) nogil
    void split(const Mat& m, vector[Mat]& mv) nogil
    void merge(vector[Mat]& mv, const Mat& m) nogil
    void transpose(InputArray src, OutputArray dst) nogil
    void flip(InputArray src, OutputArray dst, int flipCode) nogil



cdef extern from "opencv2/core/core.hpp" namespace "cv::Mat":
    Mat zeros(int rows, int cols, int type) nogil
    Mat zeros(Size size, int type) nogil
    Mat ones(int rows, int cols, int type) nogil
    Mat ones(Size size, int type) nogil

cdef extern from "opencv2/core/types_c.h":
    ctypedef void CvArr
    ctypedef struct CvSize:
        int width
        int height
    ctypedef struct _IplROI
    ctypedef struct _IplImage
    ctypedef struct _IplTileInfo
    ctypedef struct IplImage:
        int  nSize
        int  ID
        int  nChannels
        int  alphaChannel
        int  depth
        char colorModel[4]
        char channelSeq[4]
        int  dataOrder
        int  origin
        int  align
        int  width
        int  height
        _IplROI * roi
        _IplImage * maskROI
        void *imageId
        _IplTileInfo * tileInfo
        int  imageSize
        char *imageData
        int  widthStep
        int  BorderMode[4]
        int  BorderConst[4]
        char *imageDataOrigin


cdef extern from "opencv2/core/core_c.h":
    cdef void cvReleaseImage(IplImage ** image) nogil
    cdef IplImage* cvCreateImage(CvSize size, int depth, int channels) nogil


#cdef extern from "opencv2/imgproc/imgproc_c.h":
#    void cvResize( const CvArr* src, CvArr* dst, int interpolation) nogil


cdef extern from "opencv2/imgproc/imgproc.hpp" namespace "cv":
    void resize(InputArray src, OutputArray dst, Size dsize, double fx, double fy, int interpolation) nogil
    void cvtColor(InputArray src, OutputArray dst, int code, int dstCn) nogil
    void GaussianBlur(InputArray src, OutputArray dst, Size ksize, double sigmaX, double sigmaY, int borderType) nogil

    enum:
        INTER_NEAREST
        INTER_LINEAR
        INTER_CUBIC
        INTER_AREA
        INTER_LANCZOS4
        INTER_MAX
        WARP_INVERSE_MAP

    enum:
        BORDER_REPLICATE
        BORDER_REFLECT
        BORDER_REFLECT_101
        BORDER_TRANSPARENT
        BORDER_DEFAULT

    enum:
        COLOR_BGR2BGRA    = 0,
        COLOR_RGB2RGBA    = COLOR_BGR2BGRA,
        COLOR_BGRA2BGR    = 1,
        COLOR_RGBA2RGB    = COLOR_BGRA2BGR,
        COLOR_BGR2RGBA    = 2,
        COLOR_RGB2BGRA    = COLOR_BGR2RGBA,
        COLOR_RGBA2BGR    = 3,
        COLOR_BGRA2RGB    = COLOR_RGBA2BGR,
        COLOR_BGR2RGB     = 4,
        COLOR_RGB2BGR     = COLOR_BGR2RGB,
        COLOR_BGRA2RGBA   = 5,
        COLOR_RGBA2BGRA   = COLOR_BGRA2RGBA,
        COLOR_BGR2GRAY    = 6,
        COLOR_RGB2GRAY    = 7,
        COLOR_GRAY2BGR    = 8,
        COLOR_GRAY2RGB    = COLOR_GRAY2BGR,
        COLOR_GRAY2BGRA   = 9,
        COLOR_GRAY2RGBA   = COLOR_GRAY2BGRA,
        COLOR_BGRA2GRAY   = 10,
        COLOR_RGBA2GRAY   = 11,
        COLOR_COLORCVT_MAX  = 135

cdef extern from "opencv2/highgui/highgui.hpp" namespace "cv":
    Mat imread(string &filename, int flags) nogil
    bool imwrite(string &filename, InputArray img, const vector[int]& params) nogil

cdef extern from "opencv2/highgui/highgui_c.h":
    IplImage* cvLoadImage(const char* filename, int iscolor) nogil

    enum:
        CV_IMWRITE_JPEG_QUALITY = 1,
        CV_IMWRITE_PNG_COMPRESSION = 16,
        CV_IMWRITE_PNG_STRATEGY = 17,
        CV_IMWRITE_PNG_BILEVEL = 18,
        CV_IMWRITE_PNG_STRATEGY_DEFAULT = 0,
        CV_IMWRITE_PNG_STRATEGY_FILTERED = 1,
        CV_IMWRITE_PNG_STRATEGY_HUFFMAN_ONLY = 2,
        CV_IMWRITE_PNG_STRATEGY_RLE = 3,
        CV_IMWRITE_PNG_STRATEGY_FIXED = 4,
        CV_IMWRITE_PXM_BINARY = 32


cdef extern from "opencv2/core/types_c.h":
    enum:
        CV_8UC1
        CV_8UC2
        CV_8UC3
        CV_8UC4
        CV_32FC1
        CV_64FC1
        CV_32SC1
        CV_32SC2
        CV_32SC3
        CV_32SC4
    enum:
        CV_INTER_NN        =0
        CV_INTER_LINEAR    =1
        CV_INTER_CUBIC     =2
        CV_INTER_AREA      =3
        CV_INTER_LANCZOS4  =4


def load_image_data(bytes _url, int out_width, int out_height, int keep_ratio, int load_exif):
    cdef string urlptr = string(_url)
    cdef Mat img
    cdef int iorientation = -1
    cdef int org_width
    cdef int org_height
    cdef int width
    cdef int height
    cdef int channels
    cdef int i
    cdef char * tempbuf
    cdef Size outSize

    if not _url:
        return None

    with nogil:
        img = imread(urlptr, -1)

    if img.empty():
        return (0, 0, 'bgra', None)

    with nogil:
        if iorientation == 1:       # 1 = Horizontal (normal)
            pass
        elif iorientation == 2:     # 2 = Mirror horizontal
            flip(<InputArray>img, <OutputArray>img, 1)
        elif iorientation == 3:     # 3 = Rotate 180
            flip(<InputArray>img, <OutputArray>img, -1)
        elif iorientation == 4:     # 4 = Mirror vertical
            flip(<InputArray>img, <OutputArray>img, 0)
        elif iorientation == 5:     # 5 = Mirror horizontal and rotate 270 CW
            transpose(<InputArray>img, <OutputArray>img)
        elif iorientation == 6:     # 6 = Rotate 90 CW
            transpose(<InputArray>img, <OutputArray>img)
            flip(<InputArray>img, <OutputArray>img, 1)
        elif iorientation == 7:     # 7 = Mirror horizontal and rotate 90 CW
            transpose(<InputArray>img, <OutputArray>img)
            flip(<InputArray>img, <OutputArray>img, -1)
        elif iorientation == 8:     # 8 = Rotate 270 CW
            transpose(<InputArray>img, <OutputArray>img)
            flip(<InputArray>img, <OutputArray>img, 0)

        org_width = img.cols
        org_height = img.rows
        width = img.cols
        height = img.rows
        channels = img.channels()

        if (out_width > 0) and (out_height > 0) and ((out_width != width) or (out_height != height)):
            if keep_ratio:
                inratio = float(height)/float(width)
                if inratio < 1.0:
                    outSize.height = out_height
                    outSize.width = int(float(out_height)/inratio)
                else:
                    outSize.width = out_width
                    outSize.height = int(float(out_width)*inratio)
            else:
                outSize.width = out_width
                outSize.height = out_height

            resize(<InputArray>img, <OutputArray>img, outSize, 0, 0, CV_INTER_CUBIC)
            width = outSize.width
            height = outSize.height

    #Logger.info('load_image_data: <%s> orientation %d width x height <%d[%d] %d %d>' % (_url,iorientation, width,img.step1(0)*img.elemSize(), height, channels))

    colorspace = ''
    if channels == 4:
        r_data = PyString_FromStringAndSize(<char *> img.data, width * height * 4)
        colorspace = 'bgra'
    elif channels == 1:
        r_data = PyString_FromStringAndSize(<char *> img.data, width * height * 1)
        colorspace = 'luminance'
    else:
        r_data = PyString_FromStringAndSize(<char *> img.data, width * height * 3)
        colorspace = 'bgr'

    if not img.isContinuous() :
        Logger.info('load_image_data: not Continuous')
        tempbuf = <char *>PyString_AsString(r_data)
        with nogil:
            for i in range(height):
                memcpy(tempbuf+(width*channels*i), img.data+(img.step1(0)*img.elemSize()*i), width*channels)

    return (org_width, org_height, width, height, colorspace, r_data)


class ImageLoaderOpenCV(ImageLoaderBase):
    '''Image loader for opencv'''

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        return ('bmp', 'jpeg', 'jpe', 'jpg', 'png', 'ppm', 'tga', 'tiff')

    def __init__(self, filename, **kwargs):
        self.im_width = -1
        self.im_height = -1
        self.im_max_width = -1
        self.im_max_height = -1
        self.im_keepratio = True
        self.im_load_exif = False

        self.im_width = kwargs.get('width', -1)
        self.im_height = kwargs.get('height', -1)
        self.im_keepratio = kwargs.get('keep_ratio', True)

        self.im_width = kwargs.get('res_width', self.im_width)
        self.im_height = kwargs.get('res_height', self.im_height)
        self.load_exif = kwargs.get('load_exif', False)

        #Logger.info('ImageLoaderOpenCV: kwargs %s' % (kwargs))
        super(ImageLoaderOpenCV, self).__init__(filename, **kwargs)

    def load(self, filename, **kwargs):

        # in cache - get it from there
        self.keep_data = True
        data = Cache.get('kv.loader', filename)
        if data not in (None, False):
            # found image, if data is not here, need to reload.
            return data._data

        #Logger.info('ImageLoaderOpenCV: READING <%s>: <%s>' % (filename,kwargs))
        self._mipmap = kwargs.get('mipmap', self._mipmap)
        self._nocache = kwargs.get('nocache', self._nocache)
        self.keep_data = kwargs.get('keep_data', self.keep_data)
        self._data = None
        self.load_exif = kwargs.get('load_exif', self.load_exif)

        # FIXME: if the filename is unicode, the loader is failing.

        im_width = kwargs.get('res_width', self.im_width)
        im_height = kwargs.get('res_height', self.im_height)
        im_keepratio = kwargs.get('keep_ratio', self.im_keepratio)

        #Logger.info('ImageLoaderOpenCV: %d %d %d' % (im_width,im_height,im_keepratio))
        #Logger.info('ImageLoaderOpenCV: kwargs %s' % (kwargs))

        ret = load_image_data(str(filename), im_width, im_height, int(im_keepratio), int(self.load_exif))
        if ret is None:
            Logger.warning('ImageLoaderOpenCV: Unable to load image <%s>' % filename)
            raise Exception('Unable to load image')

        self.im_max_width, self.im_max_height, self.im_width, self.im_height, imgtype, data = ret
        if self.im_width != self.im_max_width or self.im_height != self.im_max_height:
            filename = '%s|%d|%d' % (filename, self.im_width, self.im_height)
        self.filename = filename

        imgdata = [ImageData(self.im_width, self.im_height, imgtype, data, source=filename)]

        # append to cash
        self._data = imgdata
        if not self._nocache:
            Cache.append('kv.loader', filename, self)

        return imgdata

    @staticmethod
    def can_save():
        return True

    @staticmethod
    def save(filename, width, height, fmt, pixels, flipped):
        cdef string outfile = filename
        cdef char *source = NULL
        cdef Mat img
        cdef bool vertical_flip = (flipped is True)
        cdef bool convRGB = False
        cdef vector[int] compression_params
        compression_params.push_back(CV_IMWRITE_JPEG_QUALITY)
        compression_params.push_back(97)

        data = pixels
        if type(data) is array:
            data = data.tostring()
        source = <bytes>data[:len(data)]
        if (fmt == 'rgba') or (fmt == 'bgra'):
            img = Mat(height, width, CV_8UC4, source)
        else:
            img = Mat(height, width, CV_8UC3, source)

        convRGB = (fmt == 'rgba') or (fmt == 'rgb')

        with nogil:
            if vertical_flip:
                flip(<InputArray>img, <OutputArray>img, 0)
            if convRGB:
                if img.channels() == 3:
                    cvtColor(<InputArray>img, <OutputArray>img, COLOR_RGB2BGR, 0)
                else:
                    cvtColor(<InputArray>img, <OutputArray>img, COLOR_RGBA2BGRA, 0)
            imwrite(outfile, <InputArray>img, compression_params)

        return True


#####################################################################################


cdef Mat createCvMat(object anImage, bool grayscale=False, bool getalpha=False):
    cdef char *source
    cdef Mat img
    cdef int readflag = 0 if grayscale else -1
    cdef vector[Mat] inmats

    if isinstance(anImage, ImageBase):
        anImage = anImage._data[0]
        width, height, fmt, data = [anImage.width, anImage.height, anImage.fmt, anImage.data]
    elif isinstance(anImage, ImageData):
        width, height, fmt, data = [anImage.width, anImage.height, anImage.fmt, anImage.data]
    elif isinstance(anImage, Texture):
        width, height, fmt, data = [anImage.width, anImage.height, 'rgba', anImage.pixels]
    elif isinstance(anImage, basestring):
        imgname = <string>anImage
        with nogil:
            img = imread(imgname, readflag)
    else:
        return img

    if img.empty():
        source = NULL
        if type(data) is array:
            data = data.tostring()
        source = <bytes>data[:len(data)]
        if (fmt == 'rgba') or (fmt == 'bgra'):
            img = Mat(height, width, CV_8UC4, source)
        else:
            img = Mat(height, width, CV_8UC3, source)

    if getalpha and img.channels() == 4:
        split(img, inmats)
        img = inmats[3]
        inmats.clear()

    return img

#######################################################################################################
